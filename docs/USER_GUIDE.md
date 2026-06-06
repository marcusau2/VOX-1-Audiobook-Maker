# VOX-1 Audiobook Maker — User Guide

## Overview

VOX-1 is a desktop application for creating audiobooks using **OmniVoice** TTS. It can:

- **Design voices** from comma-separated attribute descriptions (no audio needed)
- **Clone voices** from a short reference audio clip (3-10 seconds)
- **Render books** from TXT files, JSON manifests, EPUB, or PDF
- **Output** MP3 (single file) or M4B (with chapter markers)

---

## 1. Installation

```bash
pip install -r requirements.txt
python app.py
```

See `docs/MANUAL_INSTALL.md` for detailed instructions.

---

## 2. Interface Overview

VOX-1 has 4 tabs:

| Tab | Purpose |
|-----|---------|
| **The Lab** | Create or clone voices |
| **BookSmith** | Process EPUB/PDF files into chapter manifests |
| **The Studio** | Render audiobooks |
| **Advanced Settings** | Performance tuning |

---

## 3. The Lab — Voice Creation

### Voice Design Mode

Select **Design Voice** radio button. Enter comma-separated voice attributes and preview text, then click **Generate Preview**.

**Valid attributes:**

| Category | Options |
|----------|---------|
| Gender | `male`, `female` |
| Age | `child`, `teenager`, `young adult`, `middle-aged`, `elderly` |
| Pitch | `very low pitch`, `low pitch`, `moderate pitch`, `high pitch`, `very high pitch` |
| Style | `whisper` |
| Accent | `american accent`, `british accent`, `australian accent`, `canadian accent`, `indian accent`, `chinese accent`, `japanese accent`, `korean accent`, `portuguese accent`, `russian accent` |

**Examples:**
- `"female, british accent"`
- `"male, low pitch, american accent"`
- `"elderly, whisper"`

### Voice Clone Mode

Select **Clone Voice** radio button. Click **Choose File** to select a reference audio file (WAV or MP3, 3-10 seconds recommended). The Smart Import feature will automatically optimize the audio (strip silence, find best segment). Enter preview text and click **Generate Preview**.

### Saving Voices

After generating a preview, click **Save as Master Voice** to use it for audiobook rendering. The master voice is saved to `master_voice.wav` (or `VOX-Output/master_voice_optimized.wav` if Smart Import was used).

---

## 4. BookSmith — EPUB/PDF Processing

1. Click **Load EPUB/PDF File**
2. Select your file
3. Chapters are automatically detected and displayed with checkboxes
4. Check/uncheck chapters to include/exclude
5. Click a chapter title to preview and edit its text
6. Click **Process & Send to Studio** to prepare for rendering

The BookSmith module uses docling (for PDF) and EbookLib (for EPUB) for high-quality text extraction.

---

## 5. The Studio — Rendering

### Prerequisites
- A **Master Voice** loaded (see section 3)
- A **book** loaded (TXT, JSON manifest, or processed via BookSmith)

### Rendering Steps

1. **Load Master Voice** — Click the button or it may already be loaded from the Lab
2. **Load Book** — Click "Load Book" and select your file:
   - **TXT files** → rendered as a single MP3 file
   - **JSON manifests** → rendered as M4B with chapter markers
3. **Render Audiobook** — Click to start
4. **Stop** — Click again to stop rendering mid-process

### Output

- TXT books: `Output/<book_name>_audiobook.mp3`
- JSON manifests: `Output/<book_title>/<book_title> - <author>.m4b`

---

## 6. Advanced Settings

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| **Batch Size** | 1-64 | 2 | Text chunks processed simultaneously on GPU. Higher = faster but uses more VRAM. |
| **Chunk Size** | 100-5000 | 500 | Max characters per text segment before splitting. |
| **Guidance Scale** | 1.0-4.0 | 2.0 | How closely generation follows the voice reference. 1.0 = more variation, 4.0 = stricter adherence. |
| **Diffusion Steps** | 8-64 | 32 | Iterative refinement steps. Lower = faster but lower quality. Higher = better quality but slower. |

All settings apply instantly — no model reload needed.

### Auto-Detect Batch Size

Click **Auto-Detect Optimal Size** to get a recommended batch size based on your GPU's VRAM.

---

## 7. Tips & Troubleshooting

### Speed
- OmniVoice runs at RTF ~0.025 on an RTX 4070 Ti (40x real-time)
- A 10-hour audiobook renders in approximately 15 minutes
- Increase batch size if VRAM usage is below 50%
- Decrease batch size if you get CUDA out of memory errors

### Voice Design
- Use only the valid attribute tokens listed above — natural language like "a deep soothing voice" will not work
- Combine multiple attributes with commas: `"female, british accent, moderate pitch"`
- The valid attributes are shown in the Lab tab for reference

### Voice Cloning
- Use a clean reference recording (minimal background noise)
- 3-10 seconds is optimal — longer files are automatically trimmed to the best 5-second segment
- Smart Import processes your audio automatically

### Common Issues

**"CUDA out of memory"** — Reduce batch size in Advanced Settings, close other GPU applications, restart the app.

**App won't start** — Run `Launch-Debug.bat` to see error messages. Check that your GPU drivers support CUDA 12.8.

**Model download fails** — Check your internet connection. Models cache to `models/` and only download once.

---

## 8. Folder Structure

```
VOX-1-Audiobook-Maker/
├── app.py                  # Main application
├── backend.py              # OmniVoice TTS engine
├── booksmith_module/       # Text extraction
├── models/                 # AI model cache
├── Output/                 # Generated audiobooks
├── VOX-Output/             # Master voices
├── temp_work/              # Temporary files
├── user_settings.json      # Preferences
└── ffmpeg_bundle/          # Bundled FFmpeg
```

---

## 9. Credits

- **TTS:** [OmniVoice](https://github.com/k2-fsa/OmniVoice) by k2-fsa
- **GUI:** [CustomTkinter](https://customtkinter.tomschimansky.com/)
- **Audio:** FFmpeg, pydub, soundfile
- **Text:** EbookLib, docling, PyMuPDF, BeautifulSoup
