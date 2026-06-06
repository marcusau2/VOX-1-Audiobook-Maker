# VOX-1 Audiobook Maker

GPU-accelerated audiobook generator using **OmniVoice** TTS. Create professional audiobooks with voice design (text-to-voice from description), voice cloning (from reference audio), batch rendering, and automatic chapter management from EPUB/PDF.

![VOX-1 Interface](Github_Screenshot.png)

---

## 🚀 Quick Start

### Prerequisites

- **Windows 10/11** 64-bit
- **NVIDIA GPU** with 8GB+ VRAM (12GB recommended)
- **Python 3.12** ([scoop](https://scoop.sh/) install: `scoop install python@3.12`)
- **FFmpeg** in PATH (or bundled at `ffmpeg_bundle/ffmpeg.exe`)
- **CUDA 12.8** compatible drivers

### Install & Run

```bash
# Clone
git clone https://github.com/marcusau2/VOX-1-Audiobook-Maker.git
cd VOX-1-Audiobook-Maker

# Install dependencies
pip install -r requirements.txt

# Launch
python app.py
```

Or double-click `RUN-VOX-1.bat`.

### First Run

On first launch, the OmniVoice model (~3.5 GB) downloads automatically from HuggingFace to `models/`. Subsequent launches load instantly.

---

## 🎙️ Features

### Voice Design
Create voices from comma-separated attribute descriptions:
- `"female, british accent"`
- `"male, low pitch, american accent"`
- `"elderly, whisper"`
- Valid attributes: gender (male/female), age (child/teenager/young adult/middle-aged/elderly), pitch (very low/low/moderate/high/very high), style (whisper), accent (american/british/australian/canadian/indian/chinese/japanese/korean/portuguese/russian)

### Voice Cloning
Clone any voice from a 3-10 second reference audio sample (WAV/MP3). The OmniVoice model auto-transcribes the reference.

### Audiobook Rendering
- **TXT files** → single MP3 output
- **JSON manifests** → chapter-based M4B with embedded markers
- **EPUB/PDF** → process via BookSmith tab, then render
- Batch processing with automatic VRAM management
- Real-time factor (RTF) ~0.025 (40x real-time) on RTX 4070 Ti

---

## 📖 Usage

### 1. Create a Voice (The Lab tab)

**Design mode:** Enter comma-separated attributes + preview text → Generate Preview
**Clone mode:** Select reference audio file → Generate Preview
Save as Master Voice when satisfied.

### 2. Load Your Book (BookSmith or Studio tab)

- **BookSmith tab** — Load EPUB/PDF, select chapters, edit text, send to Studio
- **Studio tab** — Load TXT or JSON manifest directly

### 3. Render (Studio tab)

Load Master Voice + book → Click "Render Audiobook"

Output formats:
- **TXT books** → MP3
- **JSON manifests / BookSmith** → M4B with chapter markers

---

## ⚙️ Advanced Settings

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| Batch Size | 1-64 | 2 | Chunks processed simultaneously on GPU |
| Chunk Size | 100-5000 | 500 | Max characters per text segment |
| Guidance Scale | 1.0-4.0 | 2.0 | How closely generation follows reference |
| Diffusion Steps | 8-64 | 32 | Iterative refinement steps (speed vs quality) |

Settings apply instantly — no model reload needed.

---

## 📁 Project Structure

```
VOX-1-Audiobook-Maker/
├── RUN-VOX-1.bat            # Launch app
├── Launch-Debug.bat         # Launch with debug output
├── app.py                   # Main GUI (CustomTkinter)
├── backend.py               # OmniVoice TTS engine
├── requirements.txt         # Python dependencies
├── user_settings.json       # Saved preferences
├── AGENTS.md                # Development guide
├── booksmith_module/        # EPUB/PDF text extraction
│   ├── core.py              # BookData, Chapter, TextCleaner
│   └── processors.py        # EPUBProcessor, PDFProcessor
├── docs/
│   ├── USER_GUIDE.md        # Full user manual
│   └── MANUAL_INSTALL.md    # Advanced install guide
├── models/                  # AI model cache (auto-downloaded)
├── Output/                  # Generated audiobooks
├── VOX-Output/              # Master voices & optimized audio
├── temp_work/               # Temporary rendering files
├── ffmpeg_bundle/           # Bundled FFmpeg
└── system_python/           # Portable Python (optional)
```

---

## 🔄 Updating

```bash
git pull
pip install -r requirements.txt
```

Your settings and output files are preserved.

---

## 💻 System Requirements

- **OS:** Windows 10/11 64-bit
- **GPU:** NVIDIA with 8GB+ VRAM (12GB recommended, RTX 4070 Ti tested)
- **CUDA:** 12.8 compatible drivers
- **Python:** 3.12
- **Storage:** ~5 GB (app + models)
- **Internet:** Required for first-time model download only

---

## 🛠️ Tech Stack

- **TTS:** [OmniVoice](https://github.com/k2-fsa/OmniVoice) (k2-fsa/OmniVoice) — single unified model for design, clone, and rendering
- **GUI:** [CustomTkinter](https://customtkinter.tomschimansky.com/)
- **Backend:** PyTorch 2.8 + CUDA 12.8
- **Audio:** FFmpeg, pydub, soundfile
- **Text:** EbookLib, PyMuPDF, docling, BeautifulSoup

---

## 📄 License

Apache License 2.0

---

**Last Updated:** June 2026
