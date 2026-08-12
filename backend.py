import os
import sys

# --- Path hygiene -----------------------------------------------------------
# When launched from a shell that inherited PYTHONPATH (e.g. a Hermes agent
# venv, or any other interpreter's site-packages), a foreign numpy/torch can
# shadow this app's own install and crash at import with errors like
# 'No module named numpy._core._multiarray_umath' (cp311 ABI on a cp312
# interpreter). Neutralize external path pollution BEFORE importing anything
# that links against numpy. We only sanitize for the VOX-1 app itself; other
# programs are unaffected.
def _sanitize_python_path():
    try:
        import site
        own_site = [p for p in site.getsitepackages() if p]
    except Exception:
        own_site = []
    if not own_site:
        own_site = [os.path.join(sys.prefix, 'Lib', 'site-packages')]
    # Keep sys.path[0] (script dir / cwd) intact; move our own site-packages
    # to the front, ahead of any inherited foreign site-packages. Everything
    # else stays where it was.
    for p in own_site:
        if p in sys.path:
            sys.path.remove(p)
        sys.path.insert(1, p)
    # Also clear PYTHONPATH so child processes (ffmpeg, subprocess) inherit a
    # clean environment.
    os.environ.pop('PYTHONPATH', None)

_sanitize_python_path()

import torch
import soundfile as sf
import traceback
import shutil
import time
from datetime import datetime
import gc
import subprocess
import json
import hashlib
import random
import warnings

# Suppress noisy Whisper/transformers deprecation warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", message=".*clean_up_tokenization_spaces.*")
warnings.filterwarnings("ignore", message=".*force_decoder_ids.*")
warnings.filterwarnings("ignore", message=".*custom logits processor.*")
warnings.filterwarnings("ignore", message=".*Transcription using a multilingual Whisper.*")

from omnivoice import OmniVoice

# Silence transformers-specific logging (Whisper deprecation messages)
import logging
try:
    logging.getLogger("transformers").setLevel(logging.ERROR)
except Exception:
    pass

# ============================================================================
# SMART IMPORT FEATURE
# ============================================================================

def smart_import_audio(input_path, log_callback=None):
    """
    Optimizes audio file for voice cloning:
    - Finds best 5-second segment if file is long
    - Strips silence
    - Exports as WAV (Original Sample Rate)
    """
    from pydub import AudioSegment
    import numpy as np

    def log(msg):
        if log_callback:
            log_callback(msg)

    try:
        log("Smart Import: Loading audio file...")

        audio = AudioSegment.from_file(input_path)
        original_duration = len(audio) / 1000
        audio = audio.set_channels(1)
        log("Smart Import: Converted to mono (Volume untouched)")

        if len(audio) <= 20000:
            log("Smart Import: File is short, optimizing...")
            audio = strip_silence(audio, silence_thresh=-40, padding=100)
            output_dir = "VOX-Output"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, "master_voice_optimized.wav")
            audio.export(output_path, format="wav")
            duration_msg = f"{len(audio)/1000:.1f}s"
            return output_path, f"Optimized {duration_msg} clip"

        log("Smart Import: Analyzing speech patterns for best 15s clip...")
        best_segment, segment_start = find_best_speech_segment(audio, target_duration=15000)
        best_segment = strip_silence(best_segment, silence_thresh=-40, padding=100)

        output_dir = "VOX-Output"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "master_voice_optimized.wav")
        best_segment.export(output_path, format="wav")

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


def find_best_speech_segment(audio, target_duration=5000):
    from pydub import AudioSegment
    import numpy as np

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
    if rms_values.max() > 0:
        rms_values = rms_values / rms_values.max()

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
    if not nonsilent_ranges:
        return audio
    start_trim = max(0, nonsilent_ranges[0][0] - padding)
    end_trim = min(len(audio), nonsilent_ranges[-1][1] + padding)
    return audio[start_trim:end_trim].fade_in(duration=50).fade_out(duration=50)


# ============================================================================
# AUDIO ENGINE
# ============================================================================

class AudioEngine:
    def __init__(self, log_callback=print, batch_size=5, chunk_size=500,
                 guidance_scale=2.0, num_step=32, class_temperature=0.0, speed=1.0):
        self.log = log_callback
        self.batch_size = batch_size
        self.chunk_size = chunk_size

        self.guidance_scale = guidance_scale
        self.num_step = num_step
        self.class_temperature = class_temperature
        self.speed = speed

        # Background music state
        self.bg_music_enabled = False
        self.bg_music_tracks = []          # list of file paths
        self.bg_music_mode = "simple"       # "simple" or "per_chapter"
        self.bg_music_chapter_map = {}      # chapter_idx → track_idx (per_chapter mode)
        self.bg_music_volume_db = -25       # reduction in dB (negative = quieter)
        self.bg_music_fade_ms = 3000        # fade in/out duration
        self.bg_music_random = False        # random track selection (simple mode)
        self._bg_music_last_track_idx = None  # last random track to avoid immediate repeat
        self._bg_music_cache = {}           # path → AudioSegment

        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.log(f"Initializing AudioEngine on {self.device}...")

        if self.device == "cuda":
            torch.backends.cudnn.benchmark = False
            torch.backends.cudnn.deterministic = False
            torch.cuda.empty_cache()
            self._check_vram()

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
        # Opt out of HuggingFace Hub's Xet storage backend. Xet stores blobs as
        # .incomplete files and re-fetches them on every launch instead of
        # trusting the local cache, which reads as "re-downloads every time".
        # Classic (non-Xet) caching downloads each file once and reuses it.
        os.environ['HF_HUB_DISABLE_XET'] = '1'
        self.log(f"Models will be cached to: {self.models_dir}")

        self._setup_ffmpeg()

        self.model = None
        self._load_model()

    def _check_vram(self):
        try:
            total_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            used_gb = torch.cuda.memory_allocated(0) / (1024**3)
            free_gb = total_gb - used_gb
            self.log(f"GPU: {torch.cuda.get_device_name(0)}")
            self.log(f"Total VRAM: {total_gb:.1f} GB | Available: {free_gb:.1f} GB")
        except Exception as e:
            self.log(f"Could not detect VRAM: {e}")

    def _log_vram(self, stage):
        if self.device == "cuda":
            allocated = torch.cuda.memory_allocated() / 1024**3
            reserved = torch.cuda.memory_reserved() / 1024**3
            total = torch.cuda.get_device_properties(0).total_memory / 1024**3
            percent = (reserved / total) * 100
            self.log(f"[{stage}] VRAM: Alloc {allocated:.2f}GB | Rsrv {reserved:.2f}GB / {total:.1f}GB ({percent:.0f}%)")

    def _setup_ffmpeg(self):
        try:
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
            if result.returncode == 0:
                self.log("Using system ffmpeg (found in PATH)")
                return
        except Exception:
            pass

        if getattr(sys, 'frozen', False):
            bundle_dir = sys._MEIPASS
        else:
            bundle_dir = self.base_dir

        bundled = os.path.join(bundle_dir, 'ffmpeg_bundle', 'ffmpeg.exe')
        if os.path.exists(bundled):
            ffmpeg_dir = os.path.dirname(bundled)
            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ.get('PATH', '')
            self.log("Using bundled ffmpeg (system version not found)")
        else:
            self.log("WARNING: ffmpeg not found (neither system nor bundled)")

    def _load_model(self):
        model_id = "k2-fsa/OmniVoice"
        # Check whether the model is already present in the local cache BEFORE
        # calling from_pretrained, so we can report cache-hit vs. fresh
        # download and avoid the impression of re-downloading.
        cached = self._model_is_cached(model_id)
        if cached:
            self.log(f"OmniVoice model found in local cache — loading without network access...")
        else:
            self.log(f"OmniVoice model not in cache — downloading from HuggingFace ({model_id})...")
        try:
            dtype_config = torch.float16
            if self.device == "cuda":
                try:
                    major = torch.cuda.get_device_capability()[0]
                    if major >= 8:
                        dtype_config = torch.bfloat16
                        self.log(f"GPU arch {major}.x — using bfloat16")
                    else:
                        self.log(f"GPU arch {major}.x — using float16")
                except Exception:
                    self.log("Could not detect GPU arch, defaulting to float16")

            self.model = OmniVoice.from_pretrained(
                model_id,
                device_map=f"{self.device}:0" if self.device != "cpu" else self.device,
                dtype=dtype_config,
                load_asr=True,
            )
            self.log(f"OmniVoice loaded successfully. Sampling rate: {self.model.sampling_rate} Hz")
            self._log_vram("After Load")
        except Exception as e:
            self.log(f"Error loading OmniVoice: {e}")
            self.log(traceback.format_exc())
            raise

    def _model_is_cached(self, model_id):
        """Return True if the repo appears fully present in the local HF cache."""
        try:
            from huggingface_hub import scan_cache_dir
            cache = scan_cache_dir(self.models_dir)
            for repo in cache.repos:
                if repo.repo_id == model_id and repo.repo_type == "model" and repo.refs:
                    return True
        except Exception:
            pass
        # Fallback: a resolved snapshot with the weights present.
        base = os.path.join(
            self.models_dir, f"models--{model_id.replace('/', '--')}", "snapshots"
        )
        if not os.path.isdir(base):
            return False
        for name in sorted(os.listdir(base)):
            p = os.path.join(base, name)
            if os.path.isdir(p) and os.path.exists(os.path.join(p, "model.safetensors")):
                return True
        return False

    def _unload_model(self):
        if self.model is not None:
            del self.model
            self.model = None
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

    # -------------------------------------------------------------------
    # Background Music
    # -------------------------------------------------------------------

    def set_background_music(self, enabled=False, tracks=None, mode="simple",
                              chapter_map=None, volume_db=-25, fade_ms=3000,
                              randomize=False):
        """
        Configure background music for rendering.

        Args:
            enabled: whether to mix in background music
            tracks: list of file paths to music tracks
            mode: "simple" (cycle through tracks) or "per_chapter" (use chapter_map)
            chapter_map: dict of chapter_idx → track_idx
            volume_db: volume reduction in dB (negative, e.g. -25)
            fade_ms: fade in/out duration in milliseconds
            randomize: random track selection (no immediate repeat)
        """
        self.bg_music_enabled = enabled
        if tracks is not None:
            self.bg_music_tracks = list(tracks)
            # Clear cache when tracks change
            self._bg_music_cache.clear()
        self.bg_music_mode = mode
        if chapter_map is not None:
            self.bg_music_chapter_map = dict(chapter_map)
        self.bg_music_volume_db = volume_db
        self.bg_music_fade_ms = fade_ms
        self.bg_music_random = randomize
        if not randomize:
            self._bg_music_last_track_idx = None

    def _get_music_track(self, chapter_idx):
        """Determine starting track index for a chapter (per-chapter mode only)."""
        if not self.bg_music_tracks:
            return None
        if self.bg_music_mode == "per_chapter":
            return self.bg_music_chapter_map.get(chapter_idx, chapter_idx % len(self.bg_music_tracks))
        # For non-per-chapter modes, the starting track is determined during mixing
        return None

    def _pick_random_track(self):
        """Pick a random track index, avoiding immediate repeat of the last one."""
        if not self.bg_music_tracks:
            return None
        if len(self.bg_music_tracks) == 1:
            return 0
        candidates = list(range(len(self.bg_music_tracks)))
        if self._bg_music_last_track_idx is not None and len(candidates) > 1:
            candidates.remove(self._bg_music_last_track_idx)
        chosen = random.choice(candidates)
        self._bg_music_last_track_idx = chosen
        return chosen

    def _pick_sequential_track(self):
        """Pick the next track in sequence, wrapping around."""
        if not self.bg_music_tracks:
            return None
        if self._bg_music_last_track_idx is None:
            chosen = 0
        else:
            chosen = (self._bg_music_last_track_idx + 1) % len(self.bg_music_tracks)
        self._bg_music_last_track_idx = chosen
        return chosen

    def _load_music_segment(self, track_path):
        """Load a music file, caching the AudioSegment."""
        if track_path not in self._bg_music_cache:
            from pydub import AudioSegment
            seg = AudioSegment.from_file(track_path)
            if seg.channels > 1:
                seg = seg.set_channels(1)
            self._bg_music_cache[track_path] = seg
        return self._bg_music_cache[track_path]

    def _build_music_playlist(self, chapter_duration_ms, chapter_idx=0):
        """
        Build a list of (AudioSegment, is_last) for the music to fill chapter_duration_ms.
        Tracks play through naturally — when one ends, the next begins.
        """
        from pydub import AudioSegment
        playlist_segments = []
        remaining = chapter_duration_ms

        while remaining > 0:
            # Determine which track to play next
            if self.bg_music_mode == "per_chapter":
                track_idx = self._get_music_track(chapter_idx)
                if track_idx is None:
                    break
            elif self.bg_music_random:
                track_idx = self._pick_random_track()
            else:
                track_idx = self._pick_sequential_track()

            if track_idx is None or track_idx >= len(self.bg_music_tracks):
                break

            track_path = self.bg_music_tracks[track_idx]
            if not os.path.exists(track_path):
                self.log(f"Music file not found: {track_path}")
                continue

            try:
                seg = self._load_music_segment(track_path)
                # Apply volume reduction
                seg = seg + self.bg_music_volume_db

                if len(seg) <= remaining:
                    # Full track fits
                    playlist_segments.append(seg)
                    remaining -= len(seg)
                else:
                    # Last partial track
                    trimmed = seg[:remaining]
                    playlist_segments.append(trimmed)
                    remaining = 0
            except Exception as e:
                self.log(f"Error loading music track: {e}")
                continue

        return playlist_segments

    def _apply_background_music(self, audio_segment, chapter_idx=0):
        """
        Mix background music into the given audio segment.
        Builds a playlist of full tracks that play through naturally.
        When a track ends, the next random/sequential track begins.
        Returns the mixed AudioSegment (or original if music is disabled).
        """
        if not self.bg_music_enabled or not self.bg_music_tracks:
            return audio_segment

        try:
            chapter_duration = len(audio_segment)
            if chapter_duration < 100:  # Skip if chapter is tiny
                return audio_segment

            segments = self._build_music_playlist(chapter_duration, chapter_idx)
            if not segments:
                return audio_segment

            # Concatenate segments with crossfade between tracks
            crossfade_ms = min(500, chapter_duration // 4)
            if len(segments) == 1:
                music = segments[0]
            else:
                music = segments[0]
                for seg in segments[1:]:
                    cf = min(crossfade_ms, len(music), len(seg))
                    music = music.append(seg, crossfade=cf)

            # Ensure exact length match
            if len(music) > chapter_duration:
                music = music[:chapter_duration]
            elif len(music) < chapter_duration:
                from pydub import AudioSegment
                music = music + AudioSegment.silent(duration=chapter_duration - len(music))

            # Apply chapter-level fade in/out
            fade_ms = min(self.bg_music_fade_ms, chapter_duration // 2)
            if fade_ms > 0:
                music = music.fade_in(fade_ms).fade_out(fade_ms)

            # Overlay
            return audio_segment.overlay(music)

        except Exception as e:
            self.log(f"Error applying background music: {e}")
            return audio_segment

    # -------------------------------------------------------------------
    # Voice Design
    # -------------------------------------------------------------------

    def create_voice_design(self, text, description, output_filename="preview_design.wav"):
        output_path = os.path.join(self.output_dir, output_filename)
        self.log(f"Generating Voice Design...")

        audio_list = self.model.generate(
            text=text,
            instruct=description,
            guidance_scale=self.guidance_scale,
            num_step=self.num_step,
            class_temperature=self.class_temperature,
            speed=self.speed,
        )
        wav_out = audio_list[0]

        if hasattr(wav_out, 'cpu'):
            wav_cpu = wav_out.cpu().float().numpy()
        else:
            wav_cpu = wav_out

        sf.write(output_path, wav_cpu, self.model.sampling_rate)
        return output_path

    # -------------------------------------------------------------------
    # Voice Clone Preview
    # -------------------------------------------------------------------

    def create_voice_clone_preview(self, text, ref_audio_path, output_filename="preview_clone.wav"):
        output_path = os.path.join(self.output_dir, output_filename)
        self.log(f"Cloning voice...")

        audio_list = self.model.generate(
            text=text,
            ref_audio=ref_audio_path,
            guidance_scale=self.guidance_scale,
            num_step=self.num_step,
            class_temperature=self.class_temperature,
            speed=self.speed,
        )
        wav_out = audio_list[0]

        if hasattr(wav_out, 'cpu'):
            wav_cpu = wav_out.cpu().float().numpy()
        else:
            wav_cpu = wav_out

        sf.write(output_path, wav_cpu, self.model.sampling_rate)
        return output_path

    # -------------------------------------------------------------------
    # Book Rendering (TXT file)
    # -------------------------------------------------------------------

    def render_book(self, text_file_path, master_voice_path, progress_callback=None, stop_event=None):
        self.log("Step 1/3: Creating voice clone prompt...")
        voice_prompt = self.model.create_voice_clone_prompt(
            ref_audio=master_voice_path,
            ref_text=None,
        )

        self.log("Step 2/3: Reading text...")
        original_book_name = os.path.splitext(os.path.basename(text_file_path))[0]

        if text_file_path.lower().endswith((".epub", ".pdf")):
            raise RuntimeError("Please convert EPUB/PDF to TXT first or use the BookSmith tab.")

        with open(text_file_path, 'r', encoding='utf-8') as f:
            full_text = f.read()

        chunks = self._chunk_text(full_text)
        total_chunks = len(chunks)
        self.log(f"Starting render of {total_chunks} chunks.")

        indexed_chunks = [(i, c) for i, c in enumerate(chunks) if c.strip()]
        indexed_chunks.sort(key=lambda x: len(x[1]), reverse=True)

        results_cache = {}
        processed_count = 0

        for i in range(0, len(indexed_chunks), self.batch_size):
            if stop_event and stop_event.is_set():
                self.log("Render stopped by user.")
                return None

            batch_items = indexed_chunks[i:i + self.batch_size]
            batch_indices = [item[0] for item in batch_items]
            batch_texts = [item[1] for item in batch_items]

            if i % 5 == 0 and i > 0:
                gc.collect()
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()

            if i % 20 == 0:
                self._log_vram(f"Batch {i // self.batch_size}")

            try:
                batch_start = time.time()

                audio_list = self.model.generate(
                    text=batch_texts,
                    voice_clone_prompt=voice_prompt,
                    guidance_scale=self.guidance_scale,
                    num_step=self.num_step,
                    class_temperature=self.class_temperature,
                    speed=self.speed,
                )

                for idx, wav, orig_idx in zip(range(len(audio_list)), audio_list, batch_indices):
                    if hasattr(wav, 'cpu'):
                        wav_np = wav.cpu().float().numpy()
                    else:
                        wav_np = wav

                    voice_sig = os.path.basename(master_voice_path)
                    chunk_hash = hashlib.md5((chunks[orig_idx] + voice_sig).encode('utf-8')).hexdigest()[:8]
                    temp_wav = os.path.join(self.temp_dir, f"chunk_{orig_idx:04d}_{chunk_hash}.wav")
                    sf.write(temp_wav, wav_np, self.model.sampling_rate)
                    from pydub import AudioSegment
                    results_cache[orig_idx] = AudioSegment.from_wav(temp_wav)

                duration = time.time() - batch_start
                processed_count += len(batch_items)
                speed_per_chunk = duration / len(batch_items)
                progress_pct = (processed_count / total_chunks) * 100
                timestamp = datetime.now().strftime("%H:%M:%S")

                if self.device == "cuda":
                    reserved = torch.cuda.memory_reserved() / 1024**3
                    self.log(f"[{timestamp}] Done {processed_count}/{total_chunks} ({progress_pct:.0f}%) | {speed_per_chunk:.2f}s/chunk | VRAM: {reserved:.1f}GB")
                else:
                    self.log(f"[{timestamp}] Done {processed_count}/{total_chunks} ({progress_pct:.0f}%) | {speed_per_chunk:.2f}s/chunk")

                if progress_callback:
                    progress_callback(processed_count / total_chunks)

            except Exception as e:
                self.log(f"Error in batch: {e}")
                gc.collect()
                if self.device == "cuda":
                    torch.cuda.empty_cache()
                continue

        self.log("Step 3/3: Stitching audio in correct order...")
        from pydub import AudioSegment

        silence_gap = AudioSegment.silent(duration=250)
        audio_segments = []
        for i in range(total_chunks):
            if i in results_cache:
                audio_segments.append(results_cache[i])
            else:
                self.log(f"Warning: Chunk {i} failed to render.")

        if audio_segments:
            final_audio = audio_segments[0].fade_in(50).fade_out(50)
            for seg in audio_segments[1:]:
                processed_seg = seg.fade_in(50).fade_out(50)
                final_audio += silence_gap + processed_seg

            # Mix in background music (use first track for flat TXT renders)
            final_audio = self._apply_background_music(final_audio, chapter_idx=0)

            out_path = os.path.join(self.output_dir, f"{original_book_name}_audiobook.mp3")
            final_audio.export(out_path, format="mp3")
            self.log(f"SUCCESS: Saved to {out_path}")
            self._clear_temp_dir()
            return out_path
        else:
            raise RuntimeError("No audio generated.")

    # -------------------------------------------------------------------
    # Manifest-based Rendering (for BookSmith / JSON manifests)
    # -------------------------------------------------------------------

    def render_from_manifest_dict(self, manifest, master_voice_path, progress_callback=None, stop_event=None, chunk_size=None):
        return self._render_from_manifest_data(manifest, master_voice_path, progress_callback, stop_event, chunk_size=chunk_size)

    def render_from_manifest(self, json_path, master_voice_path, progress_callback=None, stop_event=None, chunk_size=None):
        with open(json_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
        return self._render_from_manifest_data(manifest, master_voice_path, progress_callback, stop_event, chunk_size=chunk_size)

    def _render_from_manifest_data(self, manifest, master_voice_path, progress_callback=None, stop_event=None, chunk_size=None):
        book_title = manifest.get("title", "Untitled")
        author = manifest.get("author", "Unknown")
        chapters_data = manifest.get("chapters", [])

        clean_title = "".join(c for c in book_title if c.isalnum() or c in ' -_').strip()
        book_output_dir = os.path.join(self.output_dir, clean_title)
        os.makedirs(book_output_dir, exist_ok=True)

        self.log("Creating voice clone prompt...")
        voice_prompt = self.model.create_voice_clone_prompt(
            ref_audio=master_voice_path,
            ref_text=None,
        )

        chapter_audio_files = []
        chapters_info = []

        for chapter_idx, chapter in enumerate(chapters_data):
            if stop_event and stop_event.is_set():
                return None

            label = chapter.get("label", f"Chapter {chapter_idx + 1}")
            text = chapter.get("text", "")
            self.log(f"Rendering: {label}")

            use_chunk_size = chunk_size if chunk_size is not None else self.chunk_size
            chunks = self._chunk_text(text, max_chars=use_chunk_size)

            indexed_chunks = [(i, c) for i, c in enumerate(chunks) if c.strip()]
            indexed_chunks.sort(key=lambda x: len(x[1]), reverse=True)

            results_cache = {}
            processed_count = 0

            for i in range(0, len(indexed_chunks), self.batch_size):
                if stop_event and stop_event.is_set():
                    return None

                batch_items = indexed_chunks[i:i + self.batch_size]
                batch_indices = [x[0] for x in batch_items]
                batch_texts = [x[1] for x in batch_items]

                if i % 5 == 0 and i > 0:
                    gc.collect()
                    if self.device == "cuda":
                        torch.cuda.empty_cache()
                        torch.cuda.synchronize()

                try:
                    batch_start = time.time()

                    audio_list = self.model.generate(
                        text=batch_texts,
                        voice_clone_prompt=voice_prompt,
                        guidance_scale=self.guidance_scale,
                        num_step=self.num_step,
                        class_temperature=self.class_temperature,
                        speed=self.speed,
                    )

                    from pydub import AudioSegment
                    for wav, idx in zip(audio_list, batch_indices):
                        if hasattr(wav, 'cpu'):
                            wav_np = wav.cpu().float().numpy()
                        else:
                            wav_np = wav

                        temp_wav = os.path.join(self.temp_dir, f"tmp_{chapter_idx}_{idx}.wav")
                        sf.write(temp_wav, wav_np, self.model.sampling_rate)
                        results_cache[idx] = AudioSegment.from_wav(temp_wav)
                        os.unlink(temp_wav)

                    duration = time.time() - batch_start
                    processed_count += len(batch_items)
                    speed = duration / len(batch_items)
                    timestamp = datetime.now().strftime("%H:%M:%S")

                    if self.device == "cuda":
                        reserved = torch.cuda.memory_reserved() / 1024**3
                        self.log(f"[{timestamp}] Done {processed_count}/{len(chunks)} | {speed:.2f}s/chunk | VRAM: {reserved:.1f}GB")
                    else:
                        self.log(f"[{timestamp}] Done {processed_count}/{len(chunks)} | {speed:.2f}s/chunk")

                except Exception as e:
                    self.log(f"Batch error: {e}")
                    gc.collect()
                    continue

            from pydub import AudioSegment
            audio_segments = []
            for i in range(len(chunks)):
                if i in results_cache:
                    audio_segments.append(results_cache[i])

            if audio_segments:
                silence_gap = AudioSegment.silent(duration=250)
                final = audio_segments[0].fade_in(50).fade_out(50)
                for s in audio_segments[1:]:
                    processed_seg = s.fade_in(50).fade_out(50)
                    final += silence_gap + processed_seg

                # Mix in background music for this chapter
                final = self._apply_background_music(final, chapter_idx=chapter_idx)

                fname = f"{chapter.get('id', chapter_idx + 1):02d}_{label}".replace(" ", "_") + ".wav"
                out_path = os.path.join(book_output_dir, fname)
                final.export(out_path, format="wav")
                chapter_audio_files.append(out_path)
                chapters_info.append({'title': label})

                if progress_callback:
                    progress_callback((chapter_idx + 1) / len(chapters_data))

            self.log(f"Chapter {chapter_idx + 1} complete. Performing memory cleanup...")
            del results_cache
            del audio_segments
            gc.collect()
            if self.device == "cuda":
                torch.cuda.empty_cache()
                torch.cuda.synchronize()

        if chapter_audio_files:
            clean_author = "".join(c for c in author if c.isalnum() or c in ' -_').strip()
            filename = f"{clean_title} - {clean_author}.m4b" if clean_author else f"{clean_title}.m4b"
            m4b_path = os.path.join(book_output_dir, filename)

            self._create_m4b_with_chapters(chapter_audio_files, chapters_info, m4b_path, book_title=book_title, artist=author)

            self.log("Cleaning up intermediate chapter files...")
            for fname in os.listdir(book_output_dir):
                if fname.endswith(".wav") or (not fname.endswith(".m4b") and not fname.endswith(".json")):
                    try:
                        full_path = os.path.join(book_output_dir, fname)
                        if os.path.isfile(full_path):
                            os.unlink(full_path)
                    except Exception:
                        pass

            return m4b_path
        else:
            raise RuntimeError("No audio generated")

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    def _clear_temp_dir(self):
        try:
            for f in os.listdir(self.temp_dir):
                fp = os.path.join(self.temp_dir, f)
                if os.path.isfile(fp):
                    os.unlink(fp)
                elif os.path.isdir(fp):
                    shutil.rmtree(fp)
        except Exception:
            pass

    def clear_converted_files(self):
        self._clear_temp_dir()

    def _chunk_text(self, text, max_chars=None):
        import re
        if max_chars is None:
            max_chars = self.chunk_size
        sentences = re.split(r'(?<=[.?!])\s+', text)
        chunks = []
        curr = ""
        for s in sentences:
            if len(s) > max_chars:
                if curr:
                    chunks.append(curr.strip())
                    curr = ""
                words = s.split()
                temp = ""
                for word in words:
                    if len(temp) + len(word) + 1 < max_chars:
                        temp += word + " "
                    else:
                        chunks.append(temp.strip())
                        temp = word + " "
                if temp:
                    chunks.append(temp.strip())
            elif len(curr) + len(s) < max_chars:
                curr += s + " "
            else:
                chunks.append(curr.strip())
                curr = s + " "
        if curr:
            chunks.append(curr.strip())
        return chunks

    def _create_m4b_with_chapters(self, chapter_audio_files, chapters_info, output_path, book_title=None, artist=None):
        from pydub import AudioSegment
        try:
            concat_file = os.path.join(self.temp_dir, "concat_list.txt")
            with open(concat_file, 'w', encoding='utf-8') as f:
                for audio_file in chapter_audio_files:
                    safe_path = audio_file.replace('\\', '/').replace("'", "'\\''")
                    f.write(f"file '{safe_path}'\n")

            updated_chapters_info = []
            cumulative_ms = 0
            for f, c in zip(chapter_audio_files, chapters_info):
                dur = len(AudioSegment.from_wav(f))
                updated_chapters_info.append({'title': c['title'], 'start_ms': cumulative_ms, 'end_ms': cumulative_ms + dur})
                cumulative_ms += dur

            metadata_file = os.path.join(self.temp_dir, "ffmetadata.txt")
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write(self._generate_ffmetadata(updated_chapters_info, book_title=book_title, artist=artist))

            cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file, '-i', metadata_file,
                   '-map_metadata', '1', '-map', '0:a', '-c:a', 'aac', '-b:a', '64k', '-y', output_path]

            process = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            if process.returncode != 0:
                self.log(f"FFMPEG Error Output:\n{process.stderr}")
                raise RuntimeError("FFMPEG failed to stitch audiobook")

            return output_path
        except Exception as e:
            self.log(f"FFMPEG Error: {e}")
            raise

    def _generate_ffmetadata(self, chapters_info, book_title=None, artist=None):
        def escape_metadata(value):
            if not value:
                return ""
            value = str(value).replace('\\', '\\\\').replace('=', '\\=').replace(';', '\\;').replace('#', '\\#')
            return value

        lines = [";FFMETADATA1"]
        if book_title:
            lines.append(f"title={escape_metadata(book_title)}")
        if artist:
            lines.append(f"artist={escape_metadata(artist)}")
        lines.append("")
        for i, chapter in enumerate(chapters_info):
            lines.append("[CHAPTER]")
            lines.append("TIMEBASE=1/1000")
            lines.append(f"START={chapter['start_ms']}")
            end = chapter['end_ms'] if 'end_ms' in chapter else (
                chapters_info[i + 1]['start_ms'] if i + 1 < len(chapters_info) else chapter['start_ms'] + 1000
            )
            lines.append(f"END={end}")
            lines.append(f"title={escape_metadata(chapter['title'])}")
            lines.append("")
        return "\n".join(lines)

    # -------------------------------------------------------------------
    # Text Extraction (EPUB / PDF)
    # -------------------------------------------------------------------

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
                if any(keyword in item_name for keyword in skip_keywords):
                    continue
                content = item.get_content()
                soup = BeautifulSoup(content, 'html.parser')
                for tag in soup.find_all(['sup', 'sub', 'script', 'style']):
                    tag.decompose()
                for tag in soup.find_all(['p', 'div', 'br']):
                    tag.append('\n')
                text = soup.get_text(separator=' ')
                text = html.unescape(text)
                lines = [re.sub(r'\s+', ' ', line).strip() for line in text.splitlines() if line.strip()]
                text = '\n\n'.join(lines)
                text = re.sub(r'\n{3,}', '\n\n', text)
                if text.strip():
                    full_text.append(text)
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
            if consecutive_nums > 0 and consecutive_nums < 5:
                consecutive_nums = 0
            if i < 100:
                if any(re.match(p, s, re.IGNORECASE) for p in [r'^Contents$', r'^Cover$', r'^Title Page$', r'^Copyright$']):
                    continue
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
                    if any(k in item.get_name().lower() for k in ['toc', 'copyright', 'cover']):
                        continue
                    soup = BeautifulSoup(item.get_content(), 'html.parser')
                    title = soup.find(['h1', 'h2'])
                    title = title.get_text().strip() if title else f"Chapter {len(chapters) + 1}"
                    text = self._sanitize_text_for_tts(html.unescape(soup.get_text(separator=' ')))
                    if len(text) > 100:
                        chapters.append({'title': title, 'text': text})
            return chapters
        except Exception:
            return None

    def _extract_chapters_from_pdf(self, pdf_path):
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(pdf_path)
            if not reader.outline:
                return None
            chapters = []
            def extract(items):
                for item in items:
                    if isinstance(item, list):
                        extract(item)
                    else:
                        try:
                            chapters.append({'title': item.title, 'page': reader.get_destination_page_number(item)})
                        except Exception:
                            pass
            extract(reader.outline)
            return chapters
        except Exception:
            return None

    def _extract_text_for_pdf_chapter(self, reader, start_page, end_page):
        import re
        full_text = []
        for p in range(start_page, end_page):
            if p < len(reader.pages):
                text = reader.pages[p].extract_text()
                if text.strip():
                    full_text.append(text)
        return self._sanitize_text_for_tts("\n\n".join(full_text))

    def _sanitize_text_for_tts(self, text):
        import re
        text = re.sub(r'[\u200b-\u200f\ufeff]', '', text)
        text = text.replace('\u201c', '"').replace('\u201d', '"').replace('\u2018', "'").replace('\u2019', "'")
        text = text.replace('\u2014', '--').replace('\u2013', '-')
        text = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', text)
        text = re.sub(r'[ \t]+', ' ', text)
        return re.sub(r'\n{3,}', '\n\n', text).strip()
