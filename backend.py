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
import hashlib

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

        output_dir = "VOX-Output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "master_voice_optimized.wav")

        best_segment.export(output_path, format="wav", parameters=["-ar", "16000"])

        start_min = int(segment_start // 60)
        start_sec = int(segment_start % 60)
        end_time = segment_start + (len(best_segment) / 1000)
        end_min = int(end_time // 60)
        end_sec = int(end_time % 60)

        time_range = f"{start_min}:{start_sec:02d}-{end_min}:{end_sec:02d}"
        return output_path, f"Extracted best {len(best_segment)/1000:.1f}s from {original_duration:.1f}s file ({time_range})"

    except Exception as e:
        if log_callback: log_callback(f"Smart Import error: {str(e)}")
        raise

def find_best_speech_segment(audio, target_duration=15000):
    samples = np.array(audio.get_array_of_samples())
    sample_rate = audio.frame_rate
    frame_length = int(sample_rate * 0.01)
    num_frames = len(samples) // frame_length

    rms_values = []
    for i in range(num_frames):
        start = i * frame_length
        end = start + frame_length
        frame = samples[start:end]
        rms = np.sqrt(np.mean(frame.astype(float) ** 2))
        rms_values.append(rms)

    rms_values = np.array(rms_values)
    if rms_values.max() > 0: rms_values = rms_values / rms_values.max()

    speech_threshold = 0.1
    window_size_ms = target_duration
    step_size_ms = 1000

    window_size_frames = int((window_size_ms / 1000) * (sample_rate / frame_length))
    step_size_frames = int((step_size_ms / 1000) * (sample_rate / frame_length))

    best_score = -1
    best_start_frame = 0

    for start_frame in range(0, max(1, num_frames - window_size_frames + 1), step_size_frames):
        end_frame = min(start_frame + window_size_frames, num_frames)
        window_rms = rms_values[start_frame:end_frame]
        speech_frames = np.sum(window_rms > speech_threshold)
        total_frames = len(window_rms)
        speech_density = speech_frames / total_frames if total_frames > 0 else 0
        
        is_speech = window_rms > speech_threshold
        transitions = np.sum(np.diff(is_speech.astype(int)) != 0)
        continuity_score = 1.0 / (1.0 + transitions * 0.1)
        
        score = speech_density * 0.7 + continuity_score * 0.3
        if score > best_score:
            best_score = score
            best_start_frame = start_frame

    start_ms = int((best_start_frame * frame_length / sample_rate) * 1000)
    end_ms = min(start_ms + window_size_ms, len(audio))
    return audio[start_ms:end_ms], start_ms / 1000

def strip_silence(audio, silence_thresh=-40, padding=200):
    from pydub.silence import detect_nonsilent
    nonsilent_ranges = detect_nonsilent(audio, min_silence_len=100, silence_thresh=silence_thresh)
    if not nonsilent_ranges: return audio
    start_trim = max(0, nonsilent_ranges[0][0] - padding)
    end_trim = min(len(audio), nonsilent_ranges[-1][1] + padding)
    return audio[start_trim:end_trim].fade_in(duration=50).fade_out(duration=50)

# ============================================================================

class AudioEngine:
    # REVERTED TO DEFAULTS: You control these via the UI now.
    def __init__(self, log_callback=print, model_size="1.7B", batch_size=5, chunk_size=500,
                 temperature=0.7, top_p=0.8, top_k=20, repetition_penalty=1.05,
                 attn_implementation="auto"):
        self.log = log_callback
        self.model_size = model_size
        self.batch_size = batch_size
        self.chunk_size = chunk_size

        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.repetition_penalty = repetition_penalty
        self.attn_implementation = attn_implementation

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.log(f"Initializing AudioEngine on {self.device}...")

        if self.device == "cuda":
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = False
            torch.cuda.empty_cache()
            self._check_vram_and_recommend()

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.temp_dir = os.path.join(self.base_dir, "temp_work")
        self.output_dir = os.path.join(self.base_dir, "Output")
        self.models_dir = os.path.join(self.base_dir, "models")

        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.models_dir, exist_ok=True)

        os.environ['HF_HOME'] = self.models_dir
        os.environ['TRANSFORMERS_CACHE'] = self.models_dir
        os.environ['HF_HUB_CACHE'] = self.models_dir
        os.environ['XDG_CACHE_HOME'] = self.models_dir
        self.log(f"Models will be cached to: {self.models_dir}")

        self._setup_ffmpeg()
        
        self.design_model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"
        self.clone_model_id = "Qwen/Qwen3-TTS-12Hz-1.7B-Base"
        self.render_model_id = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"

        self.log("Config: Voice Cloning = 1.7B, Book Rendering = 0.6B")

        self.active_model_type = None 
        self.active_model = None
        self.whisper_model = None

    def _check_vram_and_recommend(self):
        try:
            total_vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            current_vram_gb = torch.cuda.memory_allocated(0) / (1024**3)
            free_vram_gb = total_vram_gb - current_vram_gb
            self.log(f"GPU: {torch.cuda.get_device_name(0)}")
            self.log(f"Total VRAM: {total_vram_gb:.1f} GB")
            self.log(f"Available VRAM: {free_vram_gb:.1f} GB")
        except Exception as e:
            self.log(f"Could not detect VRAM: {e}")

    def _setup_ffmpeg(self):
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                self.log("Using system ffmpeg (found in PATH)")
                return
        except: pass

        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
        else:
            bundle_dir = self.base_dir

        bundled_ffmpeg = os.path.join(bundle_dir, 'ffmpeg_bundle', 'ffmpeg.exe')
        if os.path.exists(bundled_ffmpeg):
            ffmpeg_dir = os.path.dirname(bundled_ffmpeg)
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
            self.log("Using bundled ffmpeg (system version not found)")
        else:
            self.log("WARNING: ffmpeg not found (neither system nor bundled)")

    def _unload_active_model(self):
        if self.active_model is not None:
            del self.active_model
            self.active_model = None
            self.active_model_type = None
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

    def _ensure_model(self, model_type):
        if self.active_model_type == model_type: return 

        self._unload_active_model()

        if model_type == 'design':
            model_id = self.design_model_id
            self.log(f"Loading DESIGN model ({model_id})...")
        elif model_type == 'clone':
            model_id = self.clone_model_id
            self.log(f"Loading CLONE model ({model_id})...")
        else:
            model_id = self.render_model_id
            self.log(f"Loading RENDER model ({model_id})...")

        try:
            # Default to float16 (safe for Pascal/Turing/Older)
            dtype_config = torch.float16
            
            if self.device == "cuda":
                try:
                    # Check CUDA capability (Ampere is 8.0+)
                    major_version = torch.cuda.get_device_capability()[0]
                    if major_version >= 8:
                        dtype_config = torch.bfloat16
                        self.log(f"Detected modern GPU (Arch {major_version}.x) - Using bfloat16")
                    else:
                        self.log(f"Detected older GPU (Arch {major_version}.x) - Using float16")
                except:
                    self.log("Could not detect architecture, defaulting to float16")
            
            if self.attn_implementation == "auto":
                try:
                    import flash_attn
                    self.log(f"Flash Attention {flash_attn.__version__} detected")
                    self.active_model = Qwen3TTSModel.from_pretrained(
                        model_id, device_map=self.device, dtype=dtype_config,
                        attn_implementation='flash_attention_2'
                    )
                    self.log("✅ Flash Attention 2 enabled successfully")
                except ImportError:
                    self.log("Flash Attention not installed - using default")
                    self.active_model = Qwen3TTSModel.from_pretrained(
                        model_id, device_map=self.device, dtype=dtype_config
                    )
                except Exception as e:
                    self.log(f"Flash Attention failed ({str(e)[:50]}) - using default")
                    self.active_model = Qwen3TTSModel.from_pretrained(
                        model_id, device_map=self.device, dtype=dtype_config
                    )
            elif self.attn_implementation == "flash_attention_2":
                self.log(f"Forcing Flash Attention 2")
                self.active_model = Qwen3TTSModel.from_pretrained(
                    model_id, device_map=self.device, dtype=dtype_config,
                    attn_implementation='flash_attention_2'
                )
                self.log("✅ Flash Attention 2 enabled")
            elif self.attn_implementation in ["sdpa", "eager"]:
                self.log(f"Using attention method: {self.attn_implementation}")
                self.active_model = Qwen3TTSModel.from_pretrained(
                    model_id, device_map=self.device, dtype=dtype_config,
                    attn_implementation=self.attn_implementation
                )
            else:
                self.log("Using default attention implementation")
                self.active_model = Qwen3TTSModel.from_pretrained(
                    model_id, device_map=self.device, dtype=dtype_config
                )
            
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
            percent = (reserved / total) * 100
            self.log(f"[{stage}] VRAM: Alloc {allocated:.2f}GB | Rsrv {reserved:.2f}GB / {total:.1f}GB ({percent:.0f}%)")

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
        with torch.inference_mode():
            # Reduced max tokens to prevent infinite looping
            wavs, sr = self.active_model.generate_voice_design(
                text=text, language="English", instruct=description, max_new_tokens=2048
            )
            # FIX: Check if it's already a numpy array (no .cpu() needed) or a Tensor
            wav_out = wavs[0]
            if hasattr(wav_out, 'cpu'):
                wav_cpu = wav_out.cpu().float().numpy()
            else:
                wav_cpu = wav_out
            del wavs
        
        sf.write(output_path, wav_cpu, sr)
        return output_path

    def create_voice_clone_preview(self, text, ref_audio_path, output_filename="preview_clone.wav"):
        self._ensure_model('clone')
        output_path = os.path.join(self.output_dir, output_filename)
        ref_text = self._transcribe_audio(ref_audio_path)
        self.log(f"Cloning voice...")
        with torch.inference_mode():
            # Reduced max tokens to prevent infinite looping
            wavs, sr = self.active_model.generate_voice_clone(
                text=text, language="English", ref_audio=ref_audio_path, ref_text=ref_text, max_new_tokens=2048
            )
            # FIX: Check if it's already a numpy array (no .cpu() needed) or a Tensor
            wav_out = wavs[0]
            if hasattr(wav_out, 'cpu'):
                wav_cpu = wav_out.cpu().float().numpy()
            else:
                wav_cpu = wav_out
            del wavs

        sf.write(output_path, wav_cpu, sr)
        return output_path

    def render_book(self, text_file_path, master_voice_path, progress_callback=None, stop_event=None):
        self._unload_active_model()
        self._ensure_model('render')

        self.log("Step 1/3: Analyzing Master Voice...")
        ref_text = self._transcribe_audio(master_voice_path)

        # CRITICAL: Unload Whisper and SYNC to free VRAM immediately
        if self.whisper_model is not None:
            del self.whisper_model
            self.whisper_model = None
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize() # Wait for memory release
            self.log("Whisper model unloaded to free VRAM")

        voice_prompt = None
        try:
             if hasattr(self.active_model, 'create_voice_clone_prompt'):
                self.log("Optimizing voice embedding...")
                voice_prompt = self.active_model.create_voice_clone_prompt(ref_audio=master_voice_path, ref_text=ref_text)
        except Exception as e:
             self.log(f"Optimization skipped: {e}")

        self.log("Step 2/3: Reading text...")
        original_book_name = os.path.splitext(os.path.basename(text_file_path))[0]

        if text_file_path.lower().endswith((".epub", ".pdf")):
            raise RuntimeError("Please convert EPUB/PDF to TXT first or use the BookSmith tab.")

        with open(text_file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()

        chunks = self._chunk_text(full_text)
        total_chunks = len(chunks)
        self.log(f"Starting render of {total_chunks} chunks.")

        # --- SMART BATCHING ---
        indexed_chunks = [(i, c) for i, c in enumerate(chunks) if c.strip()]
        # Sort by length (Longest first) for efficient Flash Attention padding
        indexed_chunks.sort(key=lambda x: len(x[1]), reverse=True)
        
        results_cache = {}
        processed_count = 0
        
        # AUDIT: Max Tokens capped at 1536 (approx 1.5k) to prevent infinite loops
        MAX_TOKENS = 1536 
        
        with torch.inference_mode():
            for i in range(0, len(indexed_chunks), self.batch_size):
                if stop_event and stop_event.is_set():
                    self.log("Render stopped by user.")
                    return None

                batch_items = indexed_chunks[i : i + self.batch_size]
                batch_indices = [item[0] for item in batch_items]
                batch_texts = [item[1] for item in batch_items]

                # --- FIX: Periodic Cleanup (Every 5 batches) ---
                if i % 5 == 0 and i > 0:
                    gc.collect()
                    if self.device == "cuda": 
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()

                # VRAM Log
                if i % 20 == 0: self._log_vram(f"Batch {i//self.batch_size}")

                try:
                    batch_start = time.time()
                    
                    if voice_prompt is not None:
                        wavs, sr = self.active_model.generate_voice_clone(
                            text=batch_texts, language="English", voice_clone_prompt=voice_prompt,
                            max_new_tokens=MAX_TOKENS, temperature=self.temperature, top_p=self.top_p,
                            repetition_penalty=self.repetition_penalty, non_streaming_mode=True
                        )
                    else:
                        wavs, sr = self.active_model.generate_voice_clone(
                            text=batch_texts, language="English", ref_audio=master_voice_path, ref_text=ref_text,
                            max_new_tokens=MAX_TOKENS, temperature=self.temperature, top_p=self.top_p,
                            repetition_penalty=self.repetition_penalty, non_streaming_mode=True
                        )

                    # --- FIX: Move to CPU *immediately* inside loop ---
                    # This prevents the GPU tensor from persisting during disk write
                    wavs_cpu = []
                    for w in wavs:
                        if hasattr(w, "cpu"):
                            wavs_cpu.append(w.cpu().float().numpy())
                        else:
                            wavs_cpu.append(w)
                    
                    # Explicitly delete GPU reference
                    del wavs 

                    for idx, (wav, original_index) in enumerate(zip(wavs_cpu, batch_indices)):
                        voice_sig = os.path.basename(master_voice_path)
                        chunk_hash = hashlib.md5((chunks[original_index] + voice_sig).encode('utf-8')).hexdigest()[:8]
                        temp_wav = os.path.join(self.temp_dir, f"chunk_{original_index:04d}_{chunk_hash}.wav")
                        sf.write(temp_wav, wav, sr)
                        results_cache[original_index] = AudioSegment.from_wav(temp_wav)
                        
                    duration = time.time() - batch_start
                    processed_count += len(batch_items)
                    speed_per_chunk = duration / len(batch_items)
                    progress_pct = (processed_count / total_chunks) * 100
                    
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    if self.device == "cuda":
                         # CHANGED TO MEMORY_RESERVED to match Task Manager
                         reserved = torch.cuda.memory_reserved() / 1024**3
                         self.log(f"[{timestamp}] Done {processed_count}/{total_chunks} ({progress_pct:.0f}%) | {speed_per_chunk:.2f}s/chunk | VRAM: {reserved:.1f}GB")
                    else:
                         self.log(f"[{timestamp}] Done {processed_count}/{total_chunks} ({progress_pct:.0f}%) | {speed_per_chunk:.2f}s/chunk")

                    if progress_callback: 
                        progress_callback(processed_count / total_chunks)

                except Exception as e:
                    self.log(f"Error in batch: {e}")
                    # Force VRAM cleanup on error to survive
                    gc.collect()
                    if self.device == "cuda": torch.cuda.empty_cache()
                    continue

        self.log("Step 3/3: Stitching audio in correct order...")
        audio_segments = []
        for i in range(total_chunks):
            if i in results_cache:
                audio_segments.append(results_cache[i])
            else:
                self.log(f"Warning: Chunk {i} failed to render.")

        if audio_segments:
            final_audio = audio_segments[0]
            for seg in audio_segments[1:]: final_audio += seg

            out_path = os.path.join(self.output_dir, f"{original_book_name}_audiobook.mp3")
            final_audio.export(out_path, format="mp3")
            self.log(f"SUCCESS: Saved to {out_path}")
            self._clear_temp_dir()
            return out_path
        else:
            raise RuntimeError("No audio generated.")

    # ... [Helper functions for Text Extraction] ...
    def _extract_text_from_epub(self, epub_path):
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        import html
        import re
        book = epub.read_epub(epub_path)
        full_text = []
        skip_keywords = ['toc', 'copyright', 'cover', 'title', 'contents', 'dedication', 'foreword']
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                item_name = item.get_name().lower()
                if any(keyword in item_name for keyword in skip_keywords): continue
                content = item.get_content()
                soup = BeautifulSoup(content, 'html.parser')
                for tag in soup.find_all(['sup', 'sub', 'script', 'style']): tag.decompose()
                for tag in soup.find_all(['p', 'div', 'br']): tag.append('\n')
                text = soup.get_text(separator=' ')
                text = html.unescape(text)
                lines = [re.sub(r'\s+', ' ', line).strip() for line in text.splitlines() if line.strip()]
                text = '\n\n'.join(lines)
                text = re.sub(r'\n{3,}', '\n\n', text)
                if text.strip(): full_text.append(text)
        return self._skip_front_matter(self._sanitize_text_for_tts("\n\n".join(full_text)))

    def _extract_text_from_pdf(self, pdf_path):
        from PyPDF2 import PdfReader
        import re
        reader = PdfReader(pdf_path)
        full_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text.strip():
                lines = [re.sub(r'\s+', ' ', line).strip() for line in text.splitlines() if line.strip()]
                text = '\n\n'.join(lines)
                full_text.append(re.sub(r'\n{3,}', '\n\n', text))
        return self._skip_front_matter(self._sanitize_text_for_tts("\n\n".join(full_text)))

    def _skip_front_matter(self, text):
        import re
        lines = text.split('\n')
        filtered = []
        consecutive_nums = 0
        for i, line in enumerate(lines):
            s = line.strip()
            is_num = bool(re.match(r'^[0-9]+$', s)) or bool(re.match(r'^[ivxlcdmIVXLCDM]+$', s))
            if is_num and len(s) <= 4:
                consecutive_nums += 1
                continue
            if consecutive_nums > 0 and consecutive_nums < 5: consecutive_nums = 0
            if i < 100:
                if any(re.match(p, s, re.IGNORECASE) for p in [r'^Contents$', r'^Cover$', r'^Title Page$', r'^Copyright$']): continue
            filtered.append(line)
        return '\n'.join(filtered)

    def _extract_chapters_from_epub(self, epub_path):
        import ebooklib
        from ebooklib import epub
        from bs4 import BeautifulSoup
        import html
        try:
            book = epub.read_epub(epub_path)
            chapters = []
            spine_items = [book.get_item_with_id(item_id) for item_id, _ in book.spine]
            for item in spine_items:
                if item and item.get_type() == ebooklib.ITEM_DOCUMENT:
                    if any(k in item.get_name().lower() for k in ['toc', 'copyright', 'cover']): continue
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    title = soup.find(['h1', 'h2'])
                    title = title.get_text().strip() if title else f"Chapter {len(chapters)+1}"
                    text = self._sanitize_text_for_tts(html.unescape(soup.get_text(separator=' ')))
                    if len(text) > 100: chapters.append({'title': title, 'text': text})
            return chapters
        except: return None

    def _extract_chapters_from_pdf(self, pdf_path):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            if not reader.outline: return None
            chapters = []
            def extract(items):
                for item in items:
                    if isinstance(item, list): extract(item)
                    else:
                        try: chapters.append({'title': item.title, 'page': reader.get_destination_page_number(item)})
                        except: pass
            extract(reader.outline)
            return chapters
        except: return None

    def _extract_text_for_pdf_chapter(self, reader, start_page, end_page):
        import re
        full_text = []
        for p in range(start_page, end_page):
            if p < len(reader.pages):
                text = reader.pages[p].extract_text()
                if text.strip(): full_text.append(text)
        return self._sanitize_text_for_tts("\n\n".join(full_text))

    def _sanitize_text_for_tts(self, text):
        import re
        text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)
        text = text.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u2014', '--').replace('\u2013', '-')
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return re.sub(r'\n{3,}', '\n\n', text).strip()

    def _render_book_with_chapters(self, chapters, book_title, master_voice_path, ref_text, voice_prompt, progress_callback, stop_event):
        total_chapters = len(chapters)
        chapter_audio_files = []
        chapters_info = []

        self.log(f"Step 3/3: Rendering {total_chapters} chapters...")
        
        # AUDIT: Cap tokens for chapter rendering too
        MAX_TOKENS = 1536

        for chapter_idx, chapter in enumerate(chapters):
            if stop_event and stop_event.is_set(): return None
            
            chapter_title = chapter['title']
            chapter_text = chapter['text']
            self.log(f"--- Chapter {chapter_idx + 1}/{total_chapters}: {chapter_title} ---")

            chunks = self._chunk_text(chapter_text)
            
            # Smart Batching
            indexed_chunks = [(i, c) for i, c in enumerate(chunks) if c.strip()]
            indexed_chunks.sort(key=lambda x: len(x[1]), reverse=True)
            
            results_cache = {}
            processed_count = 0
            
            with torch.inference_mode():
                for i in range(0, len(indexed_chunks), self.batch_size):
                    if stop_event and stop_event.is_set(): return None
                    
                    batch_items = indexed_chunks[i : i + self.batch_size]
                    batch_indices = [item[0] for item in batch_items]
                    batch_texts = [item[1] for item in batch_items]

                    # --- FIX: Periodic Cleanup (Every 5 batches) ---
                    if i % 5 == 0 and i > 0:
                        gc.collect()
                        if self.device == "cuda": 
                            torch.cuda.empty_cache()
                            torch.cuda.synchronize()

                    try:
                        batch_start = time.time()
                        if voice_prompt is not None:
                            wavs, sr = self.active_model.generate_voice_clone(
                                text=batch_texts, language="English", voice_clone_prompt=voice_prompt,
                                max_new_tokens=MAX_TOKENS, temperature=self.temperature, top_p=self.top_p,
                                repetition_penalty=self.repetition_penalty, non_streaming_mode=True
                            )
                        else:
                            wavs, sr = self.active_model.generate_voice_clone(
                                text=batch_texts, language="English", ref_audio=master_voice_path, ref_text=ref_text,
                                max_new_tokens=MAX_TOKENS, temperature=self.temperature, top_p=self.top_p,
                                repetition_penalty=self.repetition_penalty, non_streaming_mode=True
                            )
                        
                        # --- FIX: Move to CPU *immediately* ---
                        wavs_cpu = []
                        for w in wavs:
                            if hasattr(w, "cpu"):
                                wavs_cpu.append(w.cpu().float().numpy())
                            else:
                                wavs_cpu.append(w)
                        del wavs

                        for wav, original_index in zip(wavs_cpu, batch_indices):
                            temp_wav = os.path.join(self.temp_dir, f"temp_ch{chapter_idx}_{original_index}.wav")
                            sf.write(temp_wav, wav, sr)
                            results_cache[original_index] = AudioSegment.from_wav(temp_wav)
                            os.unlink(temp_wav)
                        
                        # --- DETAILED LOGGING ---
                        duration = time.time() - batch_start
                        processed_count += len(batch_items)
                        speed = duration / len(batch_items)
                        
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        if self.device == "cuda":
                            # CHANGED TO MEMORY_RESERVED to match Task Manager
                            reserved = torch.cuda.memory_reserved() / 1024**3
                            self.log(f"[{timestamp}] Done {processed_count}/{len(chunks)} | {speed:.2f}s/chunk | VRAM: {reserved:.1f}GB")
                        else:
                            self.log(f"[{timestamp}] Done {processed_count}/{len(chunks)} | {speed:.2f}s/chunk")
                        
                        if progress_callback: progress_callback((chapter_idx + (processed_count/len(chunks))) / total_chapters)
                        
                    except Exception as e:
                        self.log(f"Error in batch: {e}")
                        gc.collect()
                        continue
            
            # Stitch
            audio_segments = []
            for i in range(len(chunks)):
                if i in results_cache: audio_segments.append(results_cache[i])
            
            if audio_segments:
                chapter_audio = audio_segments[0]
                for seg in audio_segments[1:]: chapter_audio += seg
                
                c_path = os.path.join(self.temp_dir, f"chapter_{chapter_idx:03d}.wav")
                chapter_audio.export(c_path, format="wav")
                chapter_audio_files.append(c_path)
                chapters_info.append({'title': chapter_title})
                
                # Progress update
                if progress_callback: progress_callback((chapter_idx + 1) / total_chapters)
            
            # --- FIX: HARD MEMORY RESET BETWEEN CHAPTERS ---
            self.log(f"Chapter {chapter_idx+1} complete. Performing hard memory reset...")
            del results_cache
            del audio_segments
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

        if chapter_audio_files:
            output_path = os.path.join(self.output_dir, f"{book_title}_audiobook.m4b")
            self._create_m4b_with_chapters(chapter_audio_files, chapters_info, output_path, book_title=book_title)
            return output_path
        else:
            raise RuntimeError("No audio generated.")

    def _generate_ffmetadata(self, chapters_info, book_title=None, artist=None):
        lines = [";FFMETADATA1"]
        if book_title: lines.append(f"title={book_title}")
        if artist: lines.append(f"artist={artist}")
        lines.append("")
        for i, chapter in enumerate(chapters_info):
            lines.append("[CHAPTER]")
            lines.append("TIMEBASE=1/1000")
            lines.append(f"START={chapter['start_ms']}")
            end = chapter['end_ms'] if 'end_ms' in chapter else (chapters_info[i+1]['start_ms'] if i+1 < len(chapters_info) else chapter['start_ms'] + 1000)
            lines.append(f"END={end}")
            lines.append(f"title={chapter['title']}")
            lines.append("")
        return "\n".join(lines)

    def _chunk_text(self, text, max_chars=None):
        if max_chars is None: max_chars = self.chunk_size
        sentences = re.split(r'(?<=[.?!])\s+', text)
        chunks = []
        curr = ""
        for s in sentences:
            if len(s) > max_chars:
                if curr: chunks.append(curr.strip()); curr = ""
                words = s.split()
                temp = ""
                for word in words:
                    if len(temp) + len(word) + 1 < max_chars: temp += word + " "
                    else: chunks.append(temp.strip()); temp = word + " "
                if temp: chunks.append(temp.strip())
            elif len(curr) + len(s) < max_chars: curr += s + " "
            else: chunks.append(curr.strip()); curr = s + " "
        if curr: chunks.append(curr.strip())
        return chunks

    def _create_m4b_with_chapters(self, chapter_audio_files, chapters_info, output_path, book_title=None):
        try:
            concat_file = os.path.join(self.temp_dir, "concat_list.txt")
            with open(concat_file, 'w', encoding='utf-8') as f:
                for audio_file in chapter_audio_files:
                    safe = audio_file.replace('\\', '/').replace("'", "'\\''")
                    f.write(f"file '{safe}'\n")

            updated_chapters_info = []
            cumulative_ms = 0
            for i, (f, c) in enumerate(zip(chapter_audio_files, chapters_info)):
                dur = len(AudioSegment.from_wav(f))
                updated_chapters_info.append({'title': c['title'], 'start_ms': cumulative_ms, 'end_ms': cumulative_ms + dur})
                cumulative_ms += dur

            metadata_file = os.path.join(self.temp_dir, "ffmetadata.txt")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write(self._generate_ffmetadata(updated_chapters_info, book_title=book_title))

            cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file, '-i', metadata_file,
                   '-map_metadata', '1', '-map', '0:a', '-c:a', 'aac', '-b:a', '64k', '-y', output_path]
            
            subprocess.run(cmd, capture_output=True, check=True)
            return output_path
        except Exception as e:
            self.log(f"FFMPEG Error: {e}")
            raise

    # --- RESTORED HELPER FUNCTION ---
    def render_from_manifest_dict(self, manifest, master_voice_path, progress_callback=None, stop_event=None):
        return self._render_from_manifest_data(manifest, master_voice_path, progress_callback, stop_event)

    def render_from_manifest(self, json_path, master_voice_path, progress_callback=None, stop_event=None):
        with open(json_path, 'r', encoding='utf-8') as f: manifest = json.load(f)
        return self._render_from_manifest_data(manifest, master_voice_path, progress_callback, stop_event)

    def _render_from_manifest_data(self, manifest, master_voice_path, progress_callback=None, stop_event=None):
        self._unload_active_model()
        self._ensure_model('render')
        
        book_title = manifest.get("title", "Untitled")
        chapters_data = manifest.get("chapters", [])
        book_output_dir = os.path.join(self.output_dir, "".join(c for c in book_title if c.isalnum() or c in ' -_').strip())
        os.makedirs(book_output_dir, exist_ok=True)

        ref_text = self._transcribe_audio(master_voice_path)
        
        # CRITICAL: Unload Whisper and SYNC
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
            if hasattr(self.active_model, 'create_voice_clone_prompt'):
                voice_prompt = self.active_model.create_voice_clone_prompt(ref_audio=master_voice_path, ref_text=ref_text)
        except: pass

        chapter_audio_files = []
        chapters_info = []
        
        # AUDIT: Cap tokens to prevent loops
        MAX_TOKENS = 1536

        for chapter_idx, chapter in enumerate(chapters_data):
            if stop_event and stop_event.is_set(): return None
            
            label = chapter.get("label", f"Chapter {chapter_idx+1}")
            text = chapter.get("text", "")
            style = chapter.get("style_prompt", "")
            self.log(f"Rendering: {label}")

            chunks = self._chunk_text(text)
            
            # Smart Batching
            indexed_chunks = [(i, (f"{style}\n\n{c}" if style else c)) for i, c in enumerate(chunks) if c.strip()]
            indexed_chunks.sort(key=lambda x: len(x[1]), reverse=True)
            
            results_cache = {}
            processed_count = 0
            
            with torch.inference_mode():
                for i in range(0, len(indexed_chunks), self.batch_size):
                    if stop_event and stop_event.is_set(): return None
                    
                    batch_items = indexed_chunks[i : i+self.batch_size]
                    batch_indices = [x[0] for x in batch_items]
                    batch_texts = [x[1] for x in batch_items]

                    # --- FIX: Periodic Cleanup (Every 5 batches) ---
                    if i % 5 == 0 and i > 0:
                        gc.collect()
                        if self.device == "cuda": 
                            torch.cuda.empty_cache()
                            torch.cuda.synchronize()

                    try:
                        batch_start = time.time()
                        if voice_prompt:
                            wavs, sr = self.active_model.generate_voice_clone(
                                text=batch_texts, language="English", voice_clone_prompt=voice_prompt,
                                max_new_tokens=MAX_TOKENS, temperature=self.temperature, top_p=self.top_p, 
                                repetition_penalty=self.repetition_penalty, non_streaming_mode=True)
                        else:
                            wavs, sr = self.active_model.generate_voice_clone(
                                text=batch_texts, language="English", ref_audio=master_voice_path, ref_text=ref_text,
                                max_new_tokens=MAX_TOKENS, temperature=self.temperature, top_p=self.top_p, 
                                repetition_penalty=self.repetition_penalty, non_streaming_mode=True)
                        
                        # --- FIX: Move to CPU *immediately* ---
                        wavs_cpu = []
                        for w in wavs:
                            if hasattr(w, "cpu"):
                                wavs_cpu.append(w.cpu().float().numpy())
                            else:
                                wavs_cpu.append(w)
                        del wavs

                        for wav, idx in zip(wavs_cpu, batch_indices):
                            temp_wav = os.path.join(self.temp_dir, f"tmp_{chapter_idx}_{idx}.wav")
                            sf.write(temp_wav, wav, sr)
                            results_cache[idx] = AudioSegment.from_wav(temp_wav)
                            os.unlink(temp_wav)

                        # --- DETAILED LOGGING ---
                        duration = time.time() - batch_start
                        processed_count += len(batch_items)
                        speed = duration / len(batch_items)
                        
                        timestamp = datetime.now().strftime("%H:%M:%S")
                        if self.device == "cuda":
                            # CHANGED TO MEMORY_RESERVED to match Task Manager
                            reserved = torch.cuda.memory_reserved() / 1024**3
                            self.log(f"[{timestamp}] Done {processed_count}/{len(chunks)} | {speed:.2f}s/chunk | VRAM: {reserved:.1f}GB")
                        else:
                            self.log(f"[{timestamp}] Done {processed_count}/{len(chunks)} | {speed:.2f}s/chunk")
                            
                    except Exception as e:
                        self.log(f"Batch error: {e}")
                        gc.collect()
                        continue

            audio_segments = []
            for i in range(len(chunks)):
                if i in results_cache: audio_segments.append(results_cache[i])

            if audio_segments:
                final = audio_segments[0]
                for s in audio_segments[1:]: final += s
                
                fname = f"{chapter.get('id', chapter_idx+1):02d}_{label}".replace(" ", "_") + ".wav"
                out_path = os.path.join(book_output_dir, fname)
                final.export(out_path, format="wav")
                chapter_audio_files.append(out_path)
                chapters_info.append({'title': label})
                
                if progress_callback: progress_callback((chapter_idx+1)/len(chapters_data))
            
            # --- FIX: HARD MEMORY RESET BETWEEN CHAPTERS ---
            self.log(f"Chapter {chapter_idx+1} complete. Performing hard memory reset...")
            del results_cache
            del audio_segments
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

        if chapter_audio_files:
            m4b_path = os.path.join(book_output_dir, f"{book_title}.m4b")
            self._create_m4b_with_chapters(chapter_audio_files, chapters_info, m4b_path, book_title=book_title)
            return m4b_path
        else:
            raise RuntimeError("No audio generated")

    def _clear_temp_dir(self):
        try:
            for f in os.listdir(self.temp_dir):
                fp = os.path.join(self.temp_dir, f)
                if os.path.isfile(fp): os.unlink(fp)
                elif os.path.isdir(fp): shutil.rmtree(fp)
        except: pass
    
    def clear_converted_files(self):
        self._clear_temp_dir()
