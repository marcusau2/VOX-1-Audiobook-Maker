import os
import sys
import torch
import soundfile as sf
import whisper
from qwen_tts import Qwen3TTSModel
from pydub import AudioSegment
import numpy as np
import re
import traceback
import shutil
import time
from datetime import datetime
import gc
import subprocess
import json

# ============================================================================
# SMART IMPORT FEATURE
# ============================================================================

def smart_import_audio(input_path, log_callback=None):
    """
    Optimizes audio file for voice cloning:
    - Normalizes volume to -20 dBFS
    - Finds best 15-second segment if file is long
    - Strips silence
    - Exports as 16kHz mono WAV

    Args:
        input_path: Path to input audio file (.wav or .mp3)
        log_callback: Optional logging function

    Returns:
        (output_path, info_message): Path to optimized file and user-friendly info message
    """
    def log(msg):
        if log_callback:
            log_callback(msg)

    try:
        log("Smart Import: Loading audio file...")

        # 1. Load audio
        audio = AudioSegment.from_file(input_path)
        original_duration = len(audio) / 1000  # Convert to seconds

        # 2. Convert to mono and normalize volume
        audio = audio.set_channels(1)
        change_in_dBFS = -20 - audio.dBFS
        audio = audio.apply_gain(change_in_dBFS)
        log(f"Smart Import: Normalized volume to -20 dBFS")

        # 3. If <= 20 seconds, just strip silence and return
        if len(audio) <= 20000:  # milliseconds
            log("Smart Import: File is short, optimizing...")
            audio = strip_silence(audio, silence_thresh=-40, padding=100)

            # Create output directory if needed
            output_dir = "VOX-Output"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "master_voice_optimized.wav")

            audio.export(output_path, format="wav", parameters=["-ar", "16000"])
            duration_msg = f"{len(audio)/1000:.1f}s"
            return output_path, f"Optimized {duration_msg} clip"

        # 4. For long files, find best 15-second segment
        log("Smart Import: Analyzing speech patterns...")
        best_segment, segment_start = find_best_speech_segment(audio, target_duration=15000)
        best_segment = strip_silence(best_segment, silence_thresh=-40, padding=100)

        # 5. Export
        output_dir = "VOX-Output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "master_voice_optimized.wav")

        best_segment.export(output_path, format="wav", parameters=["-ar", "16000"])

        # Format timestamp for user feedback
        start_min = int(segment_start // 60)
        start_sec = int(segment_start % 60)
        end_time = segment_start + (len(best_segment) / 1000)
        end_min = int(end_time // 60)
        end_sec = int(end_time % 60)

        time_range = f"{start_min}:{start_sec:02d}-{end_min}:{end_sec:02d}"

        return output_path, f"Extracted best {len(best_segment)/1000:.1f}s from {original_duration:.1f}s file ({time_range})"

    except Exception as e:
        if log_callback:
            log_callback(f"Smart Import error: {str(e)}")
        raise


def find_best_speech_segment(audio, target_duration=15000):
    """
    Finds the best N-second segment with highest speech density using sliding window analysis.

    Args:
        audio: pydub AudioSegment
        target_duration: Target segment length in milliseconds (default: 15000 = 15 seconds)

    Returns:
        (best_segment, start_time_seconds): Best audio segment and its start position in seconds
    """
    # Convert to numpy array for analysis
    samples = np.array(audio.get_array_of_samples())
    sample_rate = audio.frame_rate

    # Calculate RMS energy per frame (10ms windows)
    frame_length = int(sample_rate * 0.01)  # 10ms frames
    num_frames = len(samples) // frame_length

    rms_values = []
    for i in range(num_frames):
        start = i * frame_length
        end = start + frame_length
        frame = samples[start:end]
        rms = np.sqrt(np.mean(frame.astype(float) ** 2))
        rms_values.append(rms)

    rms_values = np.array(rms_values)

    # Normalize RMS values to 0-1 range
    if rms_values.max() > 0:
        rms_values = rms_values / rms_values.max()

    # Define speech threshold (frames above this are considered speech)
    speech_threshold = 0.1  # 10% of max RMS

    # Sliding window analysis
    window_size_ms = target_duration
    step_size_ms = 1000  # 1 second step

    window_size_frames = int((window_size_ms / 1000) * (sample_rate / frame_length))
    step_size_frames = int((step_size_ms / 1000) * (sample_rate / frame_length))

    best_score = -1
    best_start_frame = 0

    # Scan through entire audio
    for start_frame in range(0, max(1, num_frames - window_size_frames + 1), step_size_frames):
        end_frame = min(start_frame + window_size_frames, num_frames)
        window_rms = rms_values[start_frame:end_frame]

        # Calculate speech density
        speech_frames = np.sum(window_rms > speech_threshold)
        total_frames = len(window_rms)
        speech_density = speech_frames / total_frames if total_frames > 0 else 0

        # Calculate continuity bonus (penalize fragmentation)
        # Count transitions from speech to silence
        is_speech = window_rms > speech_threshold
        transitions = np.sum(np.diff(is_speech.astype(int)) != 0)
        continuity_score = 1.0 / (1.0 + transitions * 0.1)

        # Combined score
        score = speech_density * 0.7 + continuity_score * 0.3

        if score > best_score:
            best_score = score
            best_start_frame = start_frame

    # Extract best segment
    start_ms = int((best_start_frame * frame_length / sample_rate) * 1000)
    end_ms = min(start_ms + window_size_ms, len(audio))

    best_segment = audio[start_ms:end_ms]
    start_time_seconds = start_ms / 1000

    return best_segment, start_time_seconds


def strip_silence(audio, silence_thresh=-40, padding=200):
    """
    Strips leading and trailing silence from audio segment.

    Args:
        audio: pydub AudioSegment
        silence_thresh: Silence threshold in dBFS
        padding: Milliseconds of padding to keep at edges

    Returns:
        AudioSegment with silence stripped and smooth fades
    """
    from pydub.silence import detect_nonsilent

    # Detect non-silent chunks
    nonsilent_ranges = detect_nonsilent(
        audio,
        min_silence_len=100,  # 100ms minimum silence
        silence_thresh=silence_thresh
    )

    if not nonsilent_ranges:
        # If entire file is "silent", return as-is
        return audio

    # Get first and last non-silent positions with more padding
    start_trim = max(0, nonsilent_ranges[0][0] - padding)
    end_trim = min(len(audio), nonsilent_ranges[-1][1] + padding)

    trimmed = audio[start_trim:end_trim]

    # Add short fade-in/out to prevent pops and clicks
    trimmed = trimmed.fade_in(duration=50).fade_out(duration=50)

    return trimmed

# ============================================================================

class AudioEngine:
    def __init__(self, log_callback=print, model_size="1.7B", batch_size=3, chunk_size=500,
                 temperature=0.7, top_p=0.8, top_k=20, repetition_penalty=1.05):
        self.log = log_callback
        self.model_size = model_size
        self.batch_size = batch_size
        self.chunk_size = chunk_size

        # Generation parameters (quality/style control)
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.log(f"Initializing AudioEngine on {self.device}...")

        # Disable cudnn benchmarking - it can use excessive VRAM for workspace buffers
        if self.device == "cuda":
            torch.backends.cudnn.benchmark = False
            # self.log("Enabled cuDNN benchmarking for faster inference")

            # Detect GPU VRAM and provide recommendations
            self._check_vram_and_recommend()

        # Setup directories
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(self.base_dir, "temp_work")
        self.output_dir = os.path.join(self.base_dir, "Output")
        self.models_dir = os.path.join(self.base_dir, "models")

        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)

        # Set HuggingFace cache to local models folder (not C:\Users\...)
        os.environ['HF_HOME'] = self.models_dir
        os.environ['TRANSFORMERS_CACHE'] = self.models_dir
        os.environ['HF_HUB_CACHE'] = self.models_dir
        # Set Whisper cache to local models folder
        os.environ['XDG_CACHE_HOME'] = self.models_dir
        self.log(f"Models will be cached to: {self.models_dir}")

        # Setup ffmpeg with fallback (Option 3: check system first, use bundled as fallback)
        self._setup_ffmpeg()
        
        # Model IDs
        self.design_model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
        self.clone_model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"  # Always use 1.7B for cloning
        self.render_model_id = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"  # Always use 0.6B for rendering

        # Legacy base_model_id for backward compatibility (uses render model)
        self.base_model_id = self.render_model_id

        self.log("Config: Voice Cloning = 1.7B, Book Rendering = 0.6B")

        self.active_model_type = None # 'design', 'clone', or 'render'
        self.active_model = None
        self.whisper_model = None

    def _check_vram_and_recommend(self):
        """Check available VRAM and provide batch size recommendations."""
        try:
            total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            current_vram_gb = torch.cuda.memory_allocated(0) / (1024**3)
            free_vram_gb = total_vram_gb - current_vram_gb

            self.log(f"GPU: {torch.cuda.get_device_name(0)}")
            self.log(f"Total VRAM: {total_vram_gb:.1f} GB")
            self.log(f"Available VRAM: {free_vram_gb:.1f} GB")

            # Recommend batch size based on total VRAM
            recommended_batch = self._suggest_batch_size(total_vram_gb)
            if recommended_batch != self.batch_size:
                self.log(f"NOTE: For {total_vram_gb:.0f}GB VRAM, recommended batch size is {recommended_batch} (current: {self.batch_size})")
                self.log(f"      Adjust in Advanced Settings if needed")
            else:
                self.log(f"Current batch size ({self.batch_size}) is optimal for your GPU")

        except Exception as e:
            self.log(f"Could not detect VRAM: {e}")

    def _suggest_batch_size(self, total_vram_gb):
        """
        Suggest optimal batch size based on total VRAM.
        Conservative values based on Qwen3-TTS model testing (concurrency 1-6).

        NOTE: Qwen3-TTS batch processing has high per-chunk VRAM requirements (~5-6GB per item).
        Official testing shows concurrency levels of 1, 3, and 6 in the technical report.
        We cap at batch 3 to ensure stability across all GPU models.
        """
        if total_vram_gb >= 22:  # 4090 (24GB), 3090 (24GB)
            return 3  # Conservative - tested and proven stable
        elif total_vram_gb >= 11:  # 4070 Ti (12GB), 4080 (16GB), 3080 Ti (12GB)
            return 2  # Safe for 12-16GB cards
        elif total_vram_gb >= 7:   # 3070 (8GB), 3060 Ti (8GB)
            return 1  # Single batch for 8-10GB cards
        else:  # 6GB or less
            return 1  # Minimum

    def _setup_ffmpeg(self):
        """Check for system ffmpeg first, fall back to bundled version if not found."""
        # Check if system ffmpeg is available
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                self.log("Using system ffmpeg (found in PATH)")
                return
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # System ffmpeg not found, use bundled version
        if getattr(sys, 'frozen', False):
            # Running as compiled exe
            bundle_dir = sys._MEIPASS
        else:
            # Running as script
            bundle_dir = self.base_dir

        bundled_ffmpeg = os.path.join(bundle_dir, 'ffmpeg_bundle', 'ffmpeg.exe')
        bundled_ffprobe = os.path.join(bundle_dir, 'ffmpeg_bundle', 'ffprobe.exe')

        if os.path.exists(bundled_ffmpeg):
            # Add bundled ffmpeg to PATH
            ffmpeg_dir = os.path.dirname(bundled_ffmpeg)
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
            self.log("Using bundled ffmpeg (system version not found)")
        else:
            self.log("WARNING: ffmpeg not found (neither system nor bundled)")
            self.log("Audio processing may fail. Please install ffmpeg or ensure bundled version is included.")

    def _unload_active_model(self):
        """Forces the current model out of VRAM."""
        if self.active_model is not None:
            # self.log("Switching tasks (unloading previous model)...")
            del self.active_model
            self.active_model = None
            self.active_model_type = None
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()

    def _ensure_model(self, model_type):
        """Loads the requested model if not already loaded."""
        if self.active_model_type == model_type:
            return # Already loaded

        # Unload previous model first
        self._unload_active_model()

        if model_type == 'design':
            model_id = self.design_model_id
            self.log(f"Loading DESIGN model ({model_id})...")
        elif model_type == 'clone':
            model_id = self.clone_model_id
            self.log(f"Loading CLONE model ({model_id})...")
        else:  # 'render' or 'base' (legacy)
            model_id = self.render_model_id
            self.log(f"Loading RENDER model ({model_id})...")

        try:
            # Qwen3-TTS load
            self.active_model = Qwen3TTSModel.from_pretrained(
                model_id,
                device_map=self.device,
                dtype=torch.bfloat16
            )

            # Optimization: Compile the model if using the smaller 0.6B version for speed
            # Note: torch.compile on Windows can be unreliable, so we skip if it fails
            if "0.6B" in model_id and hasattr(torch, "compile"):
                self.log("Attempting to compile model with torch.compile()...")
                try:
                    # Try reduce-overhead mode for Windows - better compatibility
                    self.active_model = torch.compile(self.active_model, mode="reduce-overhead", fullgraph=False)
                    self.log("Model compiled successfully (reduce-overhead mode)")
                except Exception as c_err:
                    self.log(f"Compilation skipped (not critical): {str(c_err)[:100]}")
                    self.log("Continuing without compilation...")

            self.active_model_type = model_type
            self.log(f"Model loaded successfully.")
            self._log_vram("After Load")

        except Exception as e:
            self.log(f"Error loading {model_id}: {e}")
            self.log(traceback.format_exc())
            raise

    def _log_vram(self, stage):
        if self.device == "cuda":
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            
            # Utilization is based on Reserved (actual footprint)
            percent = (reserved / total) * 100
            
            self.log(f"[{stage}] VRAM: Alloc {allocated:.2f}GB | Rsrv {reserved:.2f}GB / {total:.1f}GB ({percent:.0f}%)")

    def _check_vram_available(self, required_gb=2.0):
        """Check if enough VRAM is available for next operation."""
        if self.device == "cuda":
            allocated = torch.cuda.memory_allocated() / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            available = total - allocated

            if available < required_gb:
                self.log(f"WARNING: Low VRAM! Available: {available:.2f}GB, Required: {required_gb:.1f}GB")
                # Force garbage collection
                gc.collect()
                torch.cuda.empty_cache()
                # Check again
                allocated = torch.cuda.memory_allocated() / 1024**3
                available = total - allocated
                self.log(f"After cleanup: {available:.2f}GB available")
                return available >= required_gb
            return True
        return True

    def _transcribe_audio(self, audio_path):
        if self.whisper_model is None:
            self.log("Loading Whisper model...")
            self.whisper_model = whisper.load_model("small", device=self.device)
        
        result = self.whisper_model.transcribe(audio_path)
        return result["text"].strip()

    def create_voice_design(self, text, description, output_filename="preview_design.wav"):
        self._ensure_model('design')
        output_path = os.path.join(self.output_dir, output_filename)
        self.log(f"Generating Voice Design...")
        with torch.no_grad():
            wavs, sr = self.active_model.generate_voice_design(
                text=text,
                language="English",
                instruct=description,
                max_new_tokens=4096
            )
        sf.write(output_path, wavs[0], sr)
        return output_path

    def create_voice_clone_preview(self, text, ref_audio_path, output_filename="preview_clone.wav"):
        self._ensure_model('clone')
        output_path = os.path.join(self.output_dir, output_filename)
        ref_text = self._transcribe_audio(ref_audio_path)
        self.log(f"Cloning voice...")
        with torch.no_grad():
            wavs, sr = self.active_model.generate_voice_clone(
                text=text,
                language="English",
                ref_audio=ref_audio_path,
                ref_text=ref_text,
                max_new_tokens=4096
            )
        sf.write(output_path, wavs[0], sr)
        return output_path

    def render_book(self, text_file_path, master_voice_path, progress_callback=None, stop_event=None):
        # CRITICAL: Unload any existing model to ensure fresh state
        # If we previously generated voice previews, the model can be in a corrupted state
        self._unload_active_model()

        self._ensure_model('render')

        self.log("Step 1/3: Analyzing Master Voice...")
        ref_text = self._transcribe_audio(master_voice_path)

        # CRITICAL: Unload Whisper model immediately after transcription to free ~1GB VRAM
        if self.whisper_model is not None:
            del self.whisper_model
            self.whisper_model = None
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            self.log("Whisper model unloaded to free VRAM")

        voice_prompt = None
        try:
             # Only attempt opt if we are on 1.7B, 0.6B might not support it or be buggy
             if hasattr(self.active_model, 'create_voice_clone_prompt'):
                self.log("Optimizing voice embedding...")
                voice_prompt = self.active_model.create_voice_clone_prompt(ref_audio=master_voice_path, ref_text=ref_text)
        except Exception as e:
             self.log(f"Optimization skipped (minor): {e}")

        self.log("Step 2/3: Reading text...")

        # Save original book name for final output file
        original_book_name = os.path.splitext(os.path.basename(text_file_path))[0]

        # Check file type - only TXT files are supported for now
        if text_file_path.lower().endswith(".epub"):
            self.log("ERROR: EPUB files are not supported for direct rendering.")
            self.log("")
            self.log("The Qwen3-TTS model (released Jan 2026) is very new and can hang")
            self.log("on certain text patterns found in EPUB files.")
            self.log("")
            self.log("SOLUTION: Convert your EPUB to TXT first using Calibre or similar tools:")
            self.log("  1. Open EPUB in Calibre (free: https://calibre-ebook.com)")
            self.log("  2. Click 'Convert books'")
            self.log("  3. Set output format to 'TXT'")
            self.log("  4. Click 'OK' to convert")
            self.log("  5. Load the resulting .txt file in Vox-1")
            self.log("")
            self.log("TXT files render perfectly - proven reliable with 1000+ chunks!")
            raise RuntimeError("EPUB files must be converted to TXT first. See Activity Log for instructions.")

        elif text_file_path.lower().endswith(".pdf"):
            self.log("ERROR: PDF files are not supported for direct rendering.")
            self.log("")
            self.log("The Qwen3-TTS model (released Jan 2026) is very new and can hang")
            self.log("on certain text patterns found in PDF files.")
            self.log("")
            self.log("SOLUTION: Convert your PDF to TXT first using Calibre or online tools:")
            self.log("  1. Open PDF in Calibre (free: https://calibre-ebook.com)")
            self.log("  2. Click 'Convert books'")
            self.log("  3. Set output format to 'TXT'")
            self.log("  4. Click 'OK' to convert")
            self.log("  5. Load the resulting .txt file in Vox-1")
            self.log("")
            self.log("Alternative: Use online PDF to TXT converters")
            self.log("TXT files render perfectly - proven reliable with 1000+ chunks!")
            raise RuntimeError("PDF files must be converted to TXT first. See Activity Log for instructions.")

        # TXT file processing
        self.log("Detected TXT file - processing...")
        with open(text_file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()

        chunks = self._chunk_text(full_text)
        total_chunks = len(chunks)

        self.log(f"Starting render of {total_chunks} chunks (batch_size={self.batch_size}, chunk_size={self.chunk_size}).")

        audio_segments = []
        # self._clear_temp_dir() # Removed to allow resuming

        import hashlib

        # Process chunks in batches
        with torch.no_grad():
            i = 0
            while i < total_chunks:
                if stop_event and stop_event.is_set():
                    self.log("Render stopped by user. Progress saved.")
                    return None

                # Collect batch of chunks
                batch_chunks = []
                batch_indices = []
                batch_temp_paths = []

                for b in range(self.batch_size):
                    if i + b >= total_chunks:
                        break

                    chunk = chunks[i + b]
                    if not chunk.strip():
                        continue

                    # Check cache
                    voice_sig = os.path.basename(master_voice_path)
                    chunk_hash = hashlib.md5((chunk + voice_sig).encode('utf-8')).hexdigest()[:8]
                    temp_path = os.path.join(self.temp_dir, f"chunk_{i+b:04d}_{chunk_hash}.wav")

                    if os.path.exists(temp_path):
                        try:
                            seg = AudioSegment.from_wav(temp_path)
                            audio_segments.append(seg)
                            self.log(f"Skipping chunk {i+b+1} (Cached)")
                            if progress_callback: progress_callback((i + b + 1) / total_chunks)
                            continue
                        except:
                            pass

                    batch_chunks.append(chunk)
                    batch_indices.append(i + b)
                    batch_temp_paths.append(temp_path)

                if not batch_chunks:
                    i += self.batch_size
                    continue

                # Log VRAM periodically
                if i % 20 == 0:
                    self._log_vram(f"Chunk {i}")

                # Periodic cleanup
                if i % 50 == 0 and i > 0:
                    gc.collect()
                    if self.device == "cuda":
                        torch.cuda.empty_cache()

                try:
                    batch_start = time.time()

                    # Generate audio for batch
                    if voice_prompt is not None:
                        wavs, sr = self.active_model.generate_voice_clone(
                            text=batch_chunks,
                            language="English",
                            voice_clone_prompt=voice_prompt,
                            max_new_tokens=4096,
                            temperature=self.temperature,
                            top_p=self.top_p,
                            top_k=self.top_k,
                            repetition_penalty=self.repetition_penalty
                        )
                    else:
                        wavs, sr = self.active_model.generate_voice_clone(
                            text=batch_chunks,
                            language="English",
                            ref_audio=master_voice_path,
                            ref_text=ref_text,
                            max_new_tokens=4096,
                            temperature=self.temperature,
                            top_p=self.top_p,
                            top_k=self.top_k,
                            repetition_penalty=self.repetition_penalty
                        )

                    # Save each result
                    for idx, (wav, temp_path, chunk_idx) in enumerate(zip(wavs, batch_temp_paths, batch_indices)):
                        sf.write(temp_path, wav, sr)
                        audio_segments.append(AudioSegment.from_wav(temp_path))
                        if progress_callback: progress_callback((chunk_idx + 1) / total_chunks)

                    # CRITICAL: Delete GPU tensors immediately
                    del wavs
                    if self.device == "cuda":
                        torch.cuda.empty_cache()

                    duration = time.time() - batch_start
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    # Format chunk range (e.g., "Chunks 1-3/61")
                    first_chunk = batch_indices[0] + 1
                    last_chunk = batch_indices[-1] + 1
                    chunk_range = f"{first_chunk}-{last_chunk}" if len(batch_indices) > 1 else f"{first_chunk}"

                    # Log VRAM usage with batch completion
                    if self.device == "cuda":
                        allocated = torch.cuda.memory_allocated() / 1024**3
                        total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                        percent = (allocated / total) * 100
                        self.log(f"[{timestamp}] Chunks {chunk_range}/{total_chunks} done in {duration:.2f}s ({duration/len(batch_chunks):.2f}s/chunk) | VRAM: {allocated:.2f}/{total:.1f}GB ({percent:.0f}%)")
                    else:
                        self.log(f"[{timestamp}] Chunks {chunk_range}/{total_chunks} done in {duration:.2f}s ({duration/len(batch_chunks):.2f}s/chunk)")

                except Exception as e:
                    error_msg = str(e)

                    if "out of memory" in error_msg.lower() or "cuda" in error_msg.lower():
                        self.log("")
                        self.log("=" * 70)
                        self.log("⚠️  CUDA OUT OF MEMORY ERROR ⚠️")
                        self.log("=" * 70)
                        self.log(f"Error: {e}")
                        self.log("")
                        self.log("Your GPU ran out of VRAM during generation.")
                        self.log("")
                        self.log("SOLUTIONS:")
                        self.log("  1. REDUCE BATCH SIZE: Lower it in Advanced Settings")
                        self.log("  2. USE SMALLER MODEL: Switch to 0.6B model")
                        self.log("  3. CLOSE OTHER APPLICATIONS: Free GPU memory")
                        self.log("  4. RESTART APPLICATION: Fresh start")
                        self.log("")
                        self.log("=" * 70)
                        self.log("")

                        gc.collect()
                        if self.device == "cuda":
                            torch.cuda.empty_cache()
                            torch.cuda.synchronize()

                        self.log("Attempting to recover and skip this batch...")
                        i += self.batch_size
                        continue
                    else:
                        self.log(f"Error processing batch: {e}")
                        self.log("Skipping batch and continuing...")
                        i += self.batch_size
                        continue

                i += self.batch_size
                
        self.log("Step 3/3: Stitching audio...")
        if audio_segments:
            final_audio = audio_segments[0]
            for seg in audio_segments[1:]: final_audio += seg

            # Use original book name (not the temp converted filename)
            out_path = os.path.join(self.output_dir, f"{original_book_name}_audiobook.mp3")
            final_audio.export(out_path, format="mp3")
            self.log(f"SUCCESS: Saved to {out_path}")
            self._clear_temp_dir()
            return out_path
        else:
            raise RuntimeError("No audio generated.")

    def _extract_text_from_epub(self, epub_path):
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        import html
        import re

        book = epub.read_epub(epub_path)
        full_text = []

        # Skip front matter keywords
        skip_keywords = ['toc', 'copyright', 'cover', 'title', 'contents', 'dedication', 'foreword']

        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                # Skip front matter (TOC, copyright, etc.)
                item_name = item.get_name().lower()
                if any(keyword in item_name for keyword in skip_keywords):
                    continue
                content = item.get_content()
                soup = BeautifulSoup(content, 'html.parser')

                # Remove problematic elements (like abogen does)
                for tag in soup.find_all(['sup', 'sub', 'script', 'style']):
                    tag.decompose()

                # Add paragraph breaks (preserve structure)
                for tag in soup.find_all(['p', 'div', 'br']):
                    tag.append('\n')

                # Extract text
                text = soup.get_text(separator=' ')

                # Clean the text (similar to abogen's clean_text)
                # 1. Unescape HTML entities
                text = html.unescape(text)

                # 2. Normalize whitespace on each line
                lines = []
                for line in text.splitlines():
                    line = re.sub(r'\s+', ' ', line).strip()
                    if line:  # Skip empty lines
                        lines.append(line)

                # 3. Join with proper paragraph breaks
                text = '\n\n'.join(lines)

                # 4. Replace excessive newlines with double newlines
                text = re.sub(r'\n{3,}', '\n\n', text)

                if text.strip():
                    full_text.append(text)

        combined_text = "\n\n".join(full_text)

        # Final sanitization to prevent TTS issues
        combined_text = self._sanitize_text_for_tts(combined_text)

        # Skip TOC/front matter by finding where real prose starts
        combined_text = self._skip_front_matter(combined_text)

        return combined_text

    def _extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF file using PyPDF2."""
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF support. Install with: pip install PyPDF2")

        import re

        reader = PdfReader(pdf_path)
        full_text = []

        for page_num, page in enumerate(reader.pages):
            text = page.extract_text()

            if text.strip():
                # Clean the text (similar to EPUB cleaning)
                # 1. Normalize whitespace on each line
                lines = []
                for line in text.splitlines():
                    line = re.sub(r'\s+', ' ', line).strip()
                    if line:
                        lines.append(line)

                # 2. Join with proper paragraph breaks
                text = '\n\n'.join(lines)

                # 3. Replace excessive newlines
                text = re.sub(r'\n{3,}', '\n\n', text)

                full_text.append(text)

        combined_text = "\n\n".join(full_text)

        # Final sanitization to prevent TTS issues
        combined_text = self._sanitize_text_for_tts(combined_text)

        # Skip TOC/front matter by finding where real prose starts
        combined_text = self._skip_front_matter(combined_text)

        return combined_text

    def _skip_front_matter(self, text):
        """Remove page number sequences and obvious TOC junk, but be very conservative."""
        import re

        lines = text.split('\n')
        filtered_lines = []

        # Track if we're in a sequence of standalone numbers (page numbers)
        consecutive_numbers = 0
        in_number_sequence = False

        for i, line in enumerate(lines):
            line_stripped = line.strip()

            # Check if this line is ONLY a number (page number)
            # Must be standalone: just digits, or roman numerals, nothing else
            is_standalone_number = bool(re.match(r'^[0-9]+$', line_stripped)) or \
                                  bool(re.match(r'^[ivxlcdmIVXLCDM]+$', line_stripped))

            if is_standalone_number and len(line_stripped) <= 4:
                consecutive_numbers += 1
                # If we see 5+ consecutive numbers, we're in a page number sequence
                if consecutive_numbers >= 5:
                    in_number_sequence = True
                # Skip this line (it's a page number)
                continue
            else:
                # Not a number - check if we should end the number sequence
                if consecutive_numbers > 0 and consecutive_numbers < 5:
                    # Had a few numbers but not enough to be page numbers
                    # Keep them (could be part of content)
                    in_number_sequence = False

                consecutive_numbers = 0

                # Skip very specific TOC patterns at the start of file only
                if i < 100:  # Only check first 100 lines
                    # Lines like "Contents", "Cover", "Title Page" that are standalone
                    toc_patterns = [
                        r'^Contents$',
                        r'^Cover$',
                        r'^Title Page$',
                        r'^Copyright$',
                        r'^Table of Contents$',
                        r'^Dedication$',
                        r'^Acknowledgments?$',
                        r'^Foreword$',
                        r'^Preface$'
                    ]
                    if any(re.match(pattern, line_stripped, re.IGNORECASE) for pattern in toc_patterns):
                        continue  # Skip this TOC line

                # Keep this line
                filtered_lines.append(line)

        return '\n'.join(filtered_lines)

    def _extract_chapters_from_epub(self, epub_path):
        """
        Extract chapters from EPUB file with their titles and content.
        Returns list of dicts: [{'title': 'Chapter 1', 'text': '...'}, ...]
        Returns None if no chapter structure is found.
        """
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        import html

        try:
            book = epub.read_epub(epub_path)
            chapters = []

            # Try to get structured chapters from TOC
            if hasattr(book, 'toc') and book.toc:
                self.log(f"Found {len(book.toc)} chapters in EPUB table of contents")

                def extract_toc_chapters(toc_items, depth=0):
                    """Recursively extract chapters from TOC (handles nested sections)"""
                    chapter_list = []
                    for item in toc_items:
                        if isinstance(item, tuple):
                            # Nested section (Section, [chapters])
                            section_title = item[0].title if hasattr(item[0], 'title') else str(item[0])
                            chapter_list.extend(extract_toc_chapters(item[1], depth + 1))
                        elif isinstance(item, epub.Link):
                            # Direct link to chapter
                            chapter_list.append({
                                'title': item.title,
                                'href': item.href.split('#')[0]  # Remove anchor
                            })
                        elif hasattr(item, 'title') and hasattr(item, 'href'):
                            # Chapter item with title and href
                            chapter_list.append({
                                'title': item.title,
                                'href': item.href.split('#')[0]
                            })
                    return chapter_list

                toc_chapters = extract_toc_chapters(book.toc)

                # Extract text for each TOC chapter
                for chapter_info in toc_chapters:
                    try:
                        # Find the item by href
                        item = book.get_item_with_href(chapter_info['href'])
                        if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                            content = item.get_content()
                            soup = BeautifulSoup(content, 'html.parser')

                            # Remove problematic elements
                            for tag in soup.find_all(['sup', 'sub', 'script', 'style']):
                                tag.decompose()

                            # Extract and clean text
                            text = soup.get_text(separator=' ')
                            text = html.unescape(text)
                            text = self._sanitize_text_for_tts(text)

                            if text.strip():
                                chapters.append({
                                    'title': chapter_info['title'],
                                    'text': text.strip()
                                })
                    except Exception as e:
                        self.log(f"Warning: Could not extract chapter '{chapter_info['title']}': {e}")
                        continue

            # Fallback: Use spine order if TOC didn't work
            if not chapters:
                self.log("No TOC found, using spine order for chapters")
                spine_items = [book.get_item_with_id(item_id) for item_id, _ in book.spine]

                for idx, item in enumerate(spine_items):
                    if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                        # Skip obvious front matter
                        item_name = item.get_name().lower()
                        skip_keywords = ['toc', 'copyright', 'cover', 'title']
                        if any(keyword in item_name for keyword in skip_keywords):
                            continue

                        content = item.get_content()
                        soup = BeautifulSoup(content, 'html.parser')

                        # Try to find chapter title from first h1/h2 tag
                        title_tag = soup.find(['h1', 'h2', 'h3'])
                        title = title_tag.get_text().strip() if title_tag else f"Chapter {len(chapters) + 1}"

                        # Remove problematic elements
                        for tag in soup.find_all(['sup', 'sub', 'script', 'style']):
                            tag.decompose()

                        # Extract and clean text
                        text = soup.get_text(separator=' ')
                        text = html.unescape(text)
                        text = self._sanitize_text_for_tts(text)

                        if text.strip() and len(text.strip()) > 100:  # Skip very short sections
                            chapters.append({
                                'title': title,
                                'text': text.strip()
                            })

            if chapters:
                self.log(f"Successfully extracted {len(chapters)} chapters from EPUB")
                return chapters
            else:
                self.log("No chapters found in EPUB structure")
                return None

        except Exception as e:
            self.log(f"Error extracting chapters from EPUB: {e}")
            return None

    def _extract_chapters_from_pdf(self, pdf_path):
        """
        Extract chapters from PDF bookmarks/outlines if available.
        Returns list of dicts: [{'title': 'Chapter 1', 'page': 5}, ...]
        Returns None if no bookmarks are found.
        """
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            raise ImportError("PyPDF2 is required for PDF support. Install with: pip install PyPDF2")

        try:
            reader = PdfReader(pdf_path)

            # Check if PDF has outlines/bookmarks
            if not hasattr(reader, 'outline') or not reader.outline:
                self.log("PDF has no bookmarks/table of contents")
                return None

            chapters = []

            def extract_outline(outline_items, depth=0):
                """Recursively extract bookmarks from PDF outline"""
                chapter_list = []
                for item in outline_items:
                    if isinstance(item, list):
                        # Nested section
                        chapter_list.extend(extract_outline(item, depth + 1))
                    else:
                        # Bookmark item
                        try:
                            title = item.title if hasattr(item, 'title') else str(item)
                            # Get page number (0-indexed in PyPDF2)
                            page_num = reader.get_destination_page_number(item) if hasattr(item, 'page') else 0

                            chapter_list.append({
                                'title': title,
                                'page': page_num
                            })
                        except Exception as e:
                            self.log(f"Warning: Could not extract bookmark: {e}")
                            continue
                return chapter_list

            chapters = extract_outline(reader.outline)

            if chapters:
                self.log(f"Successfully extracted {len(chapters)} chapters from PDF bookmarks")
                return chapters
            else:
                self.log("No valid bookmarks found in PDF")
                return None

        except Exception as e:
            self.log(f"Error extracting chapters from PDF: {e}")
            return None

    def _extract_text_for_pdf_chapter(self, reader, start_page, end_page):
        """Extract text from a range of PDF pages."""
        import re

        full_text = []
        for page_num in range(start_page, end_page):
            if page_num < len(reader.pages):
                page = reader.pages[page_num]
                text = page.extract_text()

                if text.strip():
                    # Clean the text
                    lines = []
                    for line in text.splitlines():
                        line = re.sub(r'\s+', ' ', line).strip()
                        if line:
                            lines.append(line)

                    text = '\n\n'.join(lines)
                    text = re.sub(r'\n{3,}', '\n\n', text)
                    full_text.append(text)

        combined_text = "\n\n".join(full_text)
        combined_text = self._sanitize_text_for_tts(combined_text)
        return combined_text

    def _sanitize_text_for_tts(self, text):
        """Clean text to prevent TTS model issues."""
        import re

        # Remove or replace problematic characters
        # 1. Remove zero-width characters and other invisible Unicode
        text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)

        # 2. Normalize quotes (smart quotes → regular quotes)
        text = text.replace('\u201c', '"').replace('\u201d', '"')  # ""
        text = text.replace('\u2018', "'").replace('\u2019', "'")  # ''

        # 3. Normalize dashes (em-dash, en-dash → regular dash)
        text = text.replace('\u2014', '--').replace('\u2013', '-')  # —–

        # 4. Remove other problematic Unicode punctuation
        text = text.replace('\u2026', '...')  # …

        # 5. Remove control characters except newlines and tabs
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)

        # 6. Normalize whitespace (but keep paragraph breaks)
        text = re.sub(r'[ \t]+', ' ', text)  # Multiple spaces/tabs → single space

        # 7. Remove excessive blank lines (more than 2 newlines in a row)
        text = re.sub(r'\n{3,}', '\n\n', text)

        return text.strip()

    def _render_book_with_chapters(self, chapters, book_title, master_voice_path, ref_text, voice_prompt, progress_callback, stop_event):
        """
        Render book with chapters, creating M4B output with chapter markers.

        Args:
            chapters: List of dicts with 'title' and 'text' keys
            book_title: Book title for metadata and filename
            master_voice_path: Path to reference voice audio
            ref_text: Transcribed text from reference voice
            voice_prompt: Optional pre-computed voice prompt
            progress_callback: Progress update callback
            stop_event: Threading event to check for stop signals
        """
        total_chapters = len(chapters)
        chapter_audio_files = []
        chapters_info = []

        self.log(f"Step 3/3: Rendering {total_chapters} chapters...")

        # Render each chapter
        for chapter_idx, chapter in enumerate(chapters):
            if stop_event and stop_event.is_set():
                self.log("Render stopped by user.")
                return None

            chapter_title = chapter['title']
            chapter_text = chapter['text']

            self.log(f"--- Chapter {chapter_idx + 1}/{total_chapters}: {chapter_title} ---")

            # Chunk the chapter text
            chunks = self._chunk_text(chapter_text)
            chunk_count = len(chunks)

            if chunk_count == 0:
                self.log(f"Skipping empty chapter: {chapter_title}")
                continue

            self.log(f"Processing {chunk_count} chunks...")

            audio_segments = []

            # Process chunks ONE AT A TIME (following ComfyUI pattern)
            with torch.no_grad():
                for i, chunk in enumerate(chunks):
                    if stop_event and stop_event.is_set():
                        self.log("Render stopped by user.")
                        return None

                    # Skip empty chunks
                    if not chunk.strip():
                        continue

                    try:
                        chunk_start = time.time()

                        # Generate audio for single chunk
                        # NOTE: Model ALWAYS returns list, even for single string input
                        if voice_prompt is not None:
                            wavs, sr = self.active_model.generate_voice_clone(
                                text=chunk,
                                language="English",
                                voice_clone_prompt=voice_prompt,
                                max_new_tokens=4096,
                                temperature=self.temperature,
                                top_p=self.top_p,
                                top_k=self.top_k,
                                repetition_penalty=self.repetition_penalty
                            )
                        else:
                            wavs, sr = self.active_model.generate_voice_clone(
                                text=chunk,
                                language="English",
                                ref_audio=master_voice_path,
                                ref_text=ref_text,
                                max_new_tokens=4096,
                                temperature=self.temperature,
                                top_p=self.top_p,
                                top_k=self.top_k,
                                repetition_penalty=self.repetition_penalty
                            )

                        # Extract wav from list (model always returns list)
                        wav = wavs[0] if isinstance(wavs, list) and len(wavs) > 0 else wavs

                        # Write to temp file then load as AudioSegment
                        temp_wav = os.path.join(self.temp_dir, f"temp_chunk_{chapter_idx}_{i}.wav")
                        sf.write(temp_wav, wav, sr)
                        audio_segments.append(AudioSegment.from_wav(temp_wav))
                        os.unlink(temp_wav)

                        # CRITICAL: Delete GPU tensors immediately after each chunk
                        del wavs, wav
                        if self.device == "cuda":
                            torch.cuda.empty_cache()

                        duration = time.time() - chunk_start
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        self.log(f"[{timestamp}] Chunk {i+1}/{chunk_count} done in {duration:.2f}s")

                        # Update overall progress
                        chapter_progress = chapter_idx / total_chapters
                        chunk_progress = ((i + 1) / chunk_count) / total_chapters
                        if progress_callback:
                            progress_callback(chapter_progress + chunk_progress)

                    except Exception as e:
                        self.log(f"Error processing chunk {i+1}: {e}")
                        continue

            # Combine chapter audio segments
            if audio_segments:
                self.log(f"Stitching chapter audio ({len(audio_segments)} chunks)...")
                chapter_audio = audio_segments[0]
                for seg in audio_segments[1:]:
                    chapter_audio += seg

                # Save chapter audio to temp file
                chapter_filename = f"chapter_{chapter_idx:03d}.wav"
                chapter_path = os.path.join(self.temp_dir, chapter_filename)
                chapter_audio.export(chapter_path, format="wav")

                chapter_audio_files.append(chapter_path)
                chapters_info.append({'title': chapter_title})

                self.log(f"✓ Chapter complete: {len(chapter_audio)/1000:.1f}s audio")
            else:
                self.log(f"Warning: No audio generated for chapter {chapter_title}")

        # Create M4B with chapters
        if chapter_audio_files:
            self.log("Creating final M4B audiobook with chapter markers...")

            output_path = os.path.join(self.output_dir, f"{book_title}_audiobook.m4b")
            self._create_m4b_with_chapters(
                chapter_audio_files,
                chapters_info,
                output_path,
                book_title=book_title
            )

            self.log(f"SUCCESS: Saved to {output_path}")
            self._clear_temp_dir()
            return output_path
        else:
            raise RuntimeError("No audio generated for any chapter.")

    def _generate_ffmetadata(self, chapters_info, book_title=None, author=None):
        """
        Generate FFMETADATA1 file content for chapter markers.

        Args:
            chapters_info: List of dicts with 'title' and 'start_ms' (and optionally 'end_ms')
            book_title: Optional book title for metadata
            author: Optional author name for metadata

        Returns:
            String content for FFMETADATA file
        """
        lines = [";FFMETADATA1"]

        # Add book metadata if available
        if book_title:
            lines.append(f"title={book_title}")
        if author:
            lines.append(f"artist={author}")

        lines.append("")  # Blank line before chapters

        # Add chapter markers
        for i, chapter in enumerate(chapters_info):
            lines.append("[CHAPTER]")
            lines.append("TIMEBASE=1/1000")
            lines.append(f"START={chapter['start_ms']}")

            # Calculate end time (use next chapter's start or provided end)
            if 'end_ms' in chapter:
                end_ms = chapter['end_ms']
            elif i + 1 < len(chapters_info):
                end_ms = chapters_info[i + 1]['start_ms']
            else:
                # Last chapter - we'll update this later with actual duration
                end_ms = chapter['start_ms'] + 1000  # Placeholder

            lines.append(f"END={end_ms}")
            lines.append(f"title={chapter['title']}")
            lines.append("")  # Blank line between chapters

        return "\n".join(lines)

    def _chunk_text(self, text, max_chars=None):
        # Use configured chunk size, or fall back to defaults
        if max_chars is None:
            max_chars = self.chunk_size

        sentences = re.split(r'(?<=[.?!])\s+', text)
        chunks = []
        curr = ""

        for s in sentences:
            # Safety: If a single sentence is too long (like TOC), hard split it
            if len(s) > max_chars:
                # Flush current chunk
                if curr:
                    chunks.append(curr.strip())
                    curr = ""

                # Split oversized sentence by words
                words = s.split()
                temp = ""
                for word in words:
                    if len(temp) + len(word) + 1 < max_chars:
                        temp += word + " "
                    else:
                        if temp:
                            chunks.append(temp.strip())
                        temp = word + " "
                if temp:
                    chunks.append(temp.strip())
                continue

            # Normal sentence processing
            if len(curr) + len(s) < max_chars:
                curr += s + " "
            else:
                if curr:
                    chunks.append(curr.strip())
                curr = s + " "

        if curr:
            chunks.append(curr.strip())

        return chunks

    def _create_m4b_with_chapters(self, chapter_audio_files, chapters_info, output_path, book_title=None):
        """
        Create M4B audiobook with chapter markers using ffmpeg.

        Args:
            chapter_audio_files: List of paths to chapter audio files (WAV format)
            chapters_info: List of dicts with 'title' and 'start_ms' keys
            output_path: Path for output M4B file
            book_title: Optional book title for metadata

        Returns:
            Path to created M4B file
        """
        try:
            # 1. Create concat file for ffmpeg
            concat_file = os.path.join(self.temp_dir, "concat_list.txt")
            with open(concat_file, 'w', encoding='utf-8') as f:
                for audio_file in chapter_audio_files:
                    # Use forward slashes and escape single quotes for ffmpeg
                    safe_path = audio_file.replace('\\', '/').replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            # 2. Calculate actual chapter durations and update end times
            updated_chapters_info = []
            cumulative_ms = 0

            for i, (audio_file, chapter) in enumerate(zip(chapter_audio_files, chapters_info)):
                # Get audio duration
                audio_seg = AudioSegment.from_wav(audio_file)
                duration_ms = len(audio_seg)

                updated_chapters_info.append({
                    'title': chapter['title'],
                    'start_ms': cumulative_ms,
                    'end_ms': cumulative_ms + duration_ms
                })

                cumulative_ms += duration_ms

            # 3. Generate FFMETADATA file
            metadata_content = self._generate_ffmetadata(
                updated_chapters_info,
                book_title=book_title
            )

            metadata_file = os.path.join(self.temp_dir, "ffmetadata.txt")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write(metadata_content)

            self.log(f"Creating M4B with {len(chapters_info)} chapters...")

            # 4. Use ffmpeg to create M4B with chapters
            # First, concatenate audio files into a single file
            temp_combined = os.path.join(self.temp_dir, "combined_audio.m4a")

            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-i', metadata_file,
                '-map_metadata', '1',  # Apply metadata from second input
                '-map', '0:a',         # Take audio from first input
                '-c:a', 'aac',         # Use AAC codec
                '-b:a', '64k',         # Bitrate (good quality for audiobooks)
                '-y',                  # Overwrite output file
                output_path
            ]

            self.log("Running ffmpeg to create M4B...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )

            if result.returncode != 0:
                self.log(f"ffmpeg error: {result.stderr}")
                raise RuntimeError(f"ffmpeg failed with code {result.returncode}")

            self.log(f"M4B created successfully: {output_path}")
            return output_path

        except Exception as e:
            self.log(f"Error creating M4B: {e}")
            raise

    def render_from_manifest_dict(self, manifest, master_voice_path, progress_callback=None, stop_event=None):
        """
        Render audiobook from manifest dictionary (BookSmith format).

        Args:
            manifest: Manifest dictionary with title, author, chapters
            master_voice_path: Path to reference voice audio
            progress_callback: Progress update callback
            stop_event: Threading event to check for stop signals

        Returns:
            Path to created M4B file
        """
        return self._render_from_manifest_data(manifest, master_voice_path, progress_callback, stop_event)

    def render_from_manifest(self, json_path, master_voice_path, progress_callback=None, stop_event=None):
        """
        Render audiobook from JSON manifest file (BookSmith format).

        Args:
            json_path: Path to JSON manifest file
            master_voice_path: Path to reference voice audio
            progress_callback: Progress update callback
            stop_event: Threading event to check for stop signals

        Returns:
            Path to created M4B file
        """
        self.log("Step 1/4: Loading JSON manifest...")

        # Load and parse JSON
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load JSON manifest: {e}")

        return self._render_from_manifest_data(manifest, master_voice_path, progress_callback, stop_event)

    def _render_from_manifest_data(self, manifest, master_voice_path, progress_callback=None, stop_event=None):
        """
        Internal method to render from manifest data.

        Args:
            manifest: Manifest dictionary
            master_voice_path: Path to reference voice audio
            progress_callback: Progress update callback
            stop_event: Threading event to check for stop signals

        Returns:
            Path to created M4B file
        """
        # CRITICAL: Unload any existing model to ensure fresh state
        # If we previously generated voice previews, the model can be in a corrupted state
        self._unload_active_model()

        self._ensure_model('render')

        # Extract metadata
        book_title = manifest.get("title", "Untitled Book")
        book_author = manifest.get("author", "Unknown Author")
        chapters_data = manifest.get("chapters", [])

        if not chapters_data:
            raise RuntimeError("JSON manifest contains no chapters!")

        self.log(f"Loaded: '{book_title}' by {book_author}")
        self.log(f"Found {len(chapters_data)} chapters")

        # Create book-specific output directory
        safe_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '-', '_')).strip()
        book_output_dir = os.path.join(self.output_dir, safe_title)
        os.makedirs(book_output_dir, exist_ok=True)

        self.log("Step 2/4: Analyzing Master Voice...")
        ref_text = self._transcribe_audio(master_voice_path)

        # CRITICAL: Unload Whisper model immediately after transcription to free ~1GB VRAM
        if self.whisper_model is not None:
            del self.whisper_model
            self.whisper_model = None
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
            self.log("Whisper model unloaded to free VRAM")

        # Optimize voice embedding if supported
        voice_prompt = None
        try:
            if hasattr(self.active_model, 'create_voice_clone_prompt'):
                self.log("Optimizing voice embedding...")
                voice_prompt = self.active_model.create_voice_clone_prompt(
                    ref_audio=master_voice_path,
                    ref_text=ref_text
                )
        except Exception as e:
            self.log(f"Optimization skipped (minor): {e}")

        self.log(f"Step 3/4: Rendering {len(chapters_data)} chapters...")

        chapter_audio_files = []
        chapters_info = []

        total_chapters = len(chapters_data)

        # Render each chapter
        for chapter_idx, chapter in enumerate(chapters_data):
            if stop_event and stop_event.is_set():
                self.log("Render stopped by user.")
                return None

            chapter_id = chapter.get("id", chapter_idx + 1)
            chapter_label = chapter.get("label", f"Chapter {chapter_id}")
            style_prompt = chapter.get("style_prompt", "").strip()
            chapter_text = chapter.get("text", "").strip()

            if not chapter_text:
                self.log(f"Skipping empty chapter: {chapter_label}")
                continue

            self.log(f"--- Chapter {chapter_idx + 1}/{total_chapters}: {chapter_label} ---")

            # Chunk the chapter text FIRST (before applying style prompt)
            chunks = self._chunk_text(chapter_text)
            chunk_count = len(chunks)

            if style_prompt:
                self.log(f"Style prompt: {style_prompt[:80]}...")
                self.log(f"Processing {chunk_count} chunks (style prompt will be applied to each)...")
            else:
                self.log(f"Processing {chunk_count} chunks...")

            audio_segments = []

            # Process chunks in batches
            with torch.no_grad():
                i = 0
                while i < chunk_count:
                    if stop_event and stop_event.is_set():
                        self.log("Render stopped by user.")
                        return None

                    # Collect batch
                    batch_chunks = []
                    batch_indices = []
                    for b in range(self.batch_size):
                        if i + b >= chunk_count:
                            break
                        chunk = chunks[i + b]
                        if not chunk.strip():
                            continue
                        # Apply style prompt if specified
                        chunk_to_generate = f"{style_prompt}\n\n{chunk}" if style_prompt else chunk
                        batch_chunks.append(chunk_to_generate)
                        batch_indices.append(i + b)

                    if not batch_chunks:
                        i += self.batch_size
                        continue

                    try:
                        batch_start = time.time()

                        # Generate audio for batch
                        if voice_prompt is not None:
                            wavs, sr = self.active_model.generate_voice_clone(
                                text=batch_chunks,
                                language="English",
                                voice_clone_prompt=voice_prompt,
                                max_new_tokens=4096,
                                temperature=self.temperature,
                                top_p=self.top_p,
                                top_k=self.top_k,
                                repetition_penalty=self.repetition_penalty
                            )
                        else:
                            wavs, sr = self.active_model.generate_voice_clone(
                                text=batch_chunks,
                                language="English",
                                ref_audio=master_voice_path,
                                ref_text=ref_text,
                                max_new_tokens=4096,
                                temperature=self.temperature,
                                top_p=self.top_p,
                                top_k=self.top_k,
                                repetition_penalty=self.repetition_penalty
                            )

                        # Save each result
                        for idx, (wav, chunk_idx) in enumerate(zip(wavs, batch_indices)):
                            temp_wav = os.path.join(self.temp_dir, f"temp_ch{chapter_idx}_{chunk_idx}.wav")
                            sf.write(temp_wav, wav, sr)
                            audio_segments.append(AudioSegment.from_wav(temp_wav))
                            os.unlink(temp_wav)

                            # Update overall progress
                            chapter_progress = chapter_idx / total_chapters
                            chunk_progress = ((chunk_idx + 1) / chunk_count) / total_chapters
                            if progress_callback:
                                progress_callback(chapter_progress + chunk_progress)

                        # CRITICAL: Delete GPU tensors immediately
                        del wavs
                        if self.device == "cuda":
                            torch.cuda.empty_cache()

                        duration = time.time() - batch_start
                        timestamp = datetime.now().strftime("%H:%M:%S")

                        # Format chunk range (e.g., "Chunks 1-3/61")
                        first_chunk = batch_indices[0] + 1
                        last_chunk = batch_indices[-1] + 1
                        chunk_range = f"{first_chunk}-{last_chunk}" if len(batch_indices) > 1 else f"{first_chunk}"

                        # Log VRAM usage with batch completion
                        if self.device == "cuda":
                            allocated = torch.cuda.memory_allocated() / 1024**3
                            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
                            percent = (allocated / total) * 100
                            self.log(f"[{timestamp}] Chunks {chunk_range}/{chunk_count} done in {duration:.2f}s ({duration/len(batch_chunks):.2f}s/chunk) | VRAM: {allocated:.2f}GB")
                            
                            # FORCE CLEANUP to prevent reserved memory fragmentation
                            torch.cuda.empty_cache()
                        else:
                            self.log(f"[{timestamp}] Chunks {chunk_range}/{chunk_count} done in {duration:.2f}s ({duration/len(batch_chunks):.2f}s/chunk)")

                    except Exception as e:
                        self.log(f"Error processing batch: {e}")
                        i += self.batch_size
                        continue

                    i += self.batch_size

            # Combine chapter audio segments
            if audio_segments:
                self.log(f"Stitching chapter audio ({len(audio_segments)} chunks)...")
                chapter_audio = audio_segments[0]
                for seg in audio_segments[1:]:
                    chapter_audio += seg

                # Save chapter audio with formatted filename
                chapter_filename = f"{chapter_id:02d}_{chapter_label}.wav"
                # Sanitize filename
                chapter_filename = "".join(c for c in chapter_filename if c.isalnum() or c in (' ', '-', '_', '.')).strip()
                chapter_path = os.path.join(book_output_dir, chapter_filename)
                chapter_audio.export(chapter_path, format="wav")

                chapter_audio_files.append(chapter_path)
                chapters_info.append({'title': chapter_label})

                self.log(f"✓ Chapter saved: {chapter_filename} ({len(chapter_audio)/1000:.1f}s audio)")
            else:
                self.log(f"Warning: No audio generated for chapter {chapter_label}")

        # Create M4B with chapters
        if chapter_audio_files:
            self.log("Step 4/4: Creating M4B audiobook with chapter markers...")

            m4b_filename = f"{safe_title}.m4b"
            output_path = os.path.join(book_output_dir, m4b_filename)

            self._create_m4b_with_chapters(
                chapter_audio_files,
                chapters_info,
                output_path,
                book_title=book_title
            )

            self.log(f"SUCCESS: Audiobook saved to {book_output_dir}")
            self.log(f"  - M4B file: {m4b_filename}")
            self.log(f"  - Individual chapters: {len(chapter_audio_files)} WAV files")

            return output_path
        else:
            raise RuntimeError("No audio generated for any chapter.")

    def _clear_temp_dir(self):
        """Clear all temp files (chunk cache and converted files)."""
        try:
            for f in os.listdir(self.temp_dir):
                fp = os.path.join(self.temp_dir, f)
                if os.path.isfile(fp): os.unlink(fp)
                elif os.path.isdir(fp): shutil.rmtree(fp)
        except:
            pass

    def clear_converted_files(self):
        """Clear only converted EPUB/PDF files (not chunk cache)."""
        try:
            converted_files = ['epub_converted.txt', 'pdf_converted.txt']
            for filename in converted_files:
                fp = os.path.join(self.temp_dir, filename)
                if os.path.exists(fp):
                    os.unlink(fp)
        except:
            pass