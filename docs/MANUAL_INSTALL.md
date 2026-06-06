# Manual Installation Guide

This guide is for developers and advanced users who want to set up VOX-1 manually.

---

## Prerequisites

- **Python 3.12** — Install via [scoop](https://scoop.sh/) (`scoop install python@3.12`) or [python.org](https://www.python.org/downloads/release/python-31210/)
- **NVIDIA GPU** with 8GB+ VRAM and CUDA 12.8 compatible drivers
- **FFmpeg** — [Download](https://ffmpeg.org/download.html) and add to PATH, or place `ffmpeg.exe` in `ffmpeg_bundle/`
- **Git** (optional, for cloning)

---

## Installation

### 1. Get the code

```bash
git clone https://github.com/marcusau2/VOX-1-Audiobook-Maker.git
cd VOX-1-Audiobook-Maker
```

Or download and extract the ZIP from GitHub.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

This installs:
- PyTorch 2.8.0+cu128 with CUDA 12.8 support
- OmniVoice TTS engine
- CustomTkinter GUI framework
- Text processing libraries (EbookLib, docling, PyMuPDF, BeautifulSoup)
- Audio processing (soundfile, pydub)

### 3. Run

```bash
python app.py
```

---

## First Run

On first launch, OmniVoice downloads the model (~3.5 GB) from HuggingFace to `models/`. This happens once — subsequent launches load from cache.

---

## CUDA Setup

VOX-1 requires CUDA 12.8 compatible drivers. The `requirements.txt` uses `--extra-index-url https://download.pytorch.org/whl/cu128` to fetch CUDA 12.8 PyTorch wheels.

To verify CUDA is working:

```bash
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

Should print `True` and your GPU name.

---

## Troubleshooting

### "No module named torch"
CUDA 12.8 wheels may not install on older CUDA drivers. Install CPU-only fallback:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### docling / PyMuPDF issues
If docling pulls incompatible PyTorch versions, re-pin after install:
```bash
pip install torch==2.8.0+cu128 torchaudio==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128
```

### FFmpeg not found
Place `ffmpeg.exe` (and `ffprobe.exe`) in `ffmpeg_bundle/` in the project root, or add FFmpeg to your system PATH.

---

## Developer Notes

### Testing the backend directly

```python
from backend import AudioEngine
engine = AudioEngine()

# Voice design
path = engine.create_voice_design("Hello world.", "male, british accent")

# Voice clone
path = engine.create_voice_clone_preview("Hello world.", "reference.wav")

# Render book
path = engine.render_book("book.txt", "master_voice.wav")
```

### Code layout

- `app.py` — CustomTkinter GUI (4 tabs)
- `backend.py` — `AudioEngine` class wrapping OmniVoice
- `booksmith_module/` — `BookData`/`Chapter` data classes, `EPUBProcessor`/`PDFProcessor`
