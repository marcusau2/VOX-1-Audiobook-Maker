# VOX-1 Audiobook Maker

GPU-accelerated audiobook generator using **OmniVoice** TTS. Create professional audiobooks with voice design, voice cloning, batch rendering, and automatic chapter management from EPUB/PDF.

![VOX-1 Interface](Github_Screenshot.png)

---

## 📢 Important Update for Existing Users

**VOX-1 has migrated from Qwen3-TTS to OmniVoice as its TTS engine.**

Previous versions used Qwen3-TTS, which suffered from a known upstream issue — deterministic audio looping during long-form generation, where the model would repeat a segment indefinitely at specific text positions ([QwenLM/Qwen3-TTS#258](https://github.com/QwenLM/Qwen3-TTS/issues/258)). Various workarounds (sampling parameter tuning, chunking adjustments) provided only partial relief.

**OmniVoice** solves this at the architecture level. It is a **non-autoregressive diffusion model** — it generates all audio tokens in parallel through iterative refinement. There is no token-level loop, no CUDA graph capture delay, and no model swapping between voice design, cloning, and rendering. Inference runs at RTF ~0.025 (40× real-time) on consumer GPUs, and the looping bug simply does not exist.

If you tried VOX-1 before and encountered looping or quality issues, those are resolved. You may want to re-clone or `git pull` to get the latest version.

---

## 🚀 Quick Start

### Prerequisites

- **Windows 10/11** 64-bit
- **NVIDIA GPU** with 8GB+ VRAM (12GB recommended, RTX 4070 Ti tested)
- **Python 3.12** — install via [scoop](https://scoop.sh/) (`scoop install python@3.12`) or [python.org](https://www.python.org/downloads/release/python-31210/)
- **FFmpeg** — [download](https://ffmpeg.org/download.html) and add to PATH, or use bundled `ffmpeg_bundle/ffmpeg.exe`
- **CUDA 12.8** compatible drivers

### Install & Run

```bash
git clone https://github.com/marcusau2/VOX-1-Audiobook-Maker.git
cd VOX-1-Audiobook-Maker
pip install -r requirements.txt
python app.py
```

Or double-click `RUN-VOX-1.bat`.

### First Run

On first launch, the OmniVoice model (~3.5 GB) downloads automatically from HuggingFace to the `models/` directory. **This is a one-time download** — subsequent launches load instantly from the local cache with no network access, and the app reports `OmniVoice model found in local cache`.

The app disables HuggingFace's experimental Xet storage backend (which could re-download blobs on every start) so that downloaded models persist and are reused across launches.

---

## 🎙️ Voice Design

Create voices from text descriptions using comma-separated attributes. No audio samples required.

### Attribute Reference

| Category | Valid Values |
|----------|-------------|
| **Gender** | `male`, `female` |
| **Age** | `child`, `teenager`, `young adult`, `middle-aged`, `elderly` |
| **Pitch** | `very low pitch`, `low pitch`, `moderate pitch`, `high pitch`, `very high pitch` |
| **Style** | `whisper` |
| **Accent** | `american accent`, `british accent`, `australian accent`, `canadian accent`, `indian accent`, `chinese accent`, `japanese accent`, `korean accent`, `portuguese accent`, `russian accent` |

### Usage

In the **Lab** tab, enter attributes in the text box as a comma-separated list:

| Example | Result |
|---------|--------|
| `female, british accent` | Female narrator with British English |
| `male, low pitch, american accent` | Deep male American voice |
| `elderly, whisper` | Quiet, aged whisper |
| `female, young adult, high pitch` | Bright young female voice |

**Note:** Attributes must use the exact tokens above. Natural language descriptions like "a deep soothing voice" are not supported by OmniVoice's attribute system — the valid options are shown directly in the app for reference.

### Voice Cloning

To clone an existing voice:
1. Switch to **Clone Voice** mode in the Lab tab
2. Load a reference audio file (WAV or MP3, 3–10 seconds recommended)
3. Enter preview text and click **Generate Preview**
4. The model auto-transcribes the reference — no manual transcription needed

---

## 📖 Usage

### Step 1: Create a Voice (The Lab tab)
- **Design mode** — Enter comma-separated attributes, enter preview text, click **Generate Preview**
- **Clone mode** — Select reference audio file, enter preview text, click **Generate Preview**
- Click **Save as Master Voice** when satisfied

### Step 2: Load Your Book
- **BookSmith tab** — Load EPUB or PDF, select chapters, edit text if needed, click **Process & Send to Studio**
- **Studio tab** — Load TXT files or JSON manifests directly

### Step 3: Render (The Studio tab)
- Load your Master Voice (if not already loaded)
- Load your book
- Click **Render Audiobook**

| Book Type | Output |
|-----------|--------|
| Plain text (.txt) | Single MP3 file |
| JSON manifest (.json) | M4B with chapter markers |
| EPUB/PDF (via BookSmith) | M4B with chapter markers |

### Background Music (The Studio tab)

VOX-1 can mix background music into rendered audiobooks *(experimental)*:

- Load one or more music files (MP3/WAV) in the Studio tab
- **Simple mode** — tracks play sequentially (or randomly, with no immediate repeats) and continue across the book
- **Per-chapter mode** — assign specific music tracks to individual chapters
- Adjust music volume (default −25 dB), chapter fade in/out duration, and track crossfade
- Music is mixed beneath the narration and baked into the final audiobook export

---

## ⚙️ Performance & Advanced Settings

OmniVoice is a diffusion model — non-autoregressive, no looping, no CUDA graph warmup needed.

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| Batch Size | 1–64 | 10 | Text chunks processed simultaneously on GPU |
| Chunk Size | 100–5000 | 250 | Max characters per text segment (250 keeps each chunk under OmniVoice's internal 30s re-split threshold for smooth output) |
| Speaking Speed | 0.5–2.0 | 1.0 | Speed of generated speech — applies to voice design, cloning, and render |
| Guidance Scale | 1.0–4.0 | 2.0 | How closely generated speech matches the reference |
| Diffusion Steps | 8–64 | 32 | Iterative refinement steps (lower = faster, higher = better quality) |

All settings apply instantly — no model reload required.

### Expected Performance

| GPU | RTF (Real-Time Factor) | 10-hour book |
|-----|------------------------|--------------|
| RTX 4070 Ti (12GB) | ~0.025 (40× real-time) | ~15 minutes |
| RTX 4090 (24GB) | ~0.02 (50× real-time, est.) | ~12 minutes |

---

## 📁 Project Structure

```
VOX-1-Audiobook-Maker/
├── RUN-VOX-1.bat            # Launch app
├── Launch-Debug.bat         # Launch with debug output
├── Setup.ps1                # Dependency installer
├── app.py                   # Main GUI (CustomTkinter)
├── backend.py               # OmniVoice TTS engine
├── requirements.txt         # Python dependencies
├── booksmith_module/        # EPUB/PDF text extraction
├── docs/
│   ├── USER_GUIDE.md        # Full user manual
│   └── MANUAL_INSTALL.md    # Advanced install guide
├── models/                  # AI model cache (auto-downloaded)
├── Output/                  # Generated audiobooks
├── temp_work/               # Temporary rendering files
└── ffmpeg_bundle/           # Bundled FFmpeg
```

---

## 🔄 Updating

```bash
git pull
pip install -r requirements.txt
```

Your settings and generated audiobooks are preserved across updates.

---

## 💻 System Requirements

- **OS:** Windows 10/11 64-bit
- **GPU:** NVIDIA with 8GB+ VRAM (12GB recommended)
- **CUDA:** 12.8 compatible drivers
- **Python:** 3.12
- **Storage:** ~5 GB (app + models + dependencies)
- **Internet:** Required for first-time model download only

---

## 🛠️ Tech Stack

- **TTS:** [OmniVoice](https://github.com/k2-fsa/OmniVoice) — single unified model for design, cloning, and rendering
- **GUI:** [CustomTkinter](https://customtkinter.tomschimansky.com/)
- **ML:** PyTorch 2.8 + CUDA 12.8
- **Audio:** FFmpeg, pydub, soundfile
- **Text:** EbookLib, PyMuPDF, docling, BeautifulSoup

---

## 📄 License

Apache License 2.0

---

**Last Updated:** August 2026
