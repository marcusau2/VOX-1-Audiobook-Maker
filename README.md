# VOX-1 Audiobook Maker

A powerful, GPU-accelerated text-to-speech audiobook generator using Qwen2-TTS models. Generate professional-quality audiobooks with multiple voice options, batch processing, and automatic chapter management.

> **Status:** Active Development (Private Alpha)
> **GPU Required:** NVIDIA GPU with 8GB+ VRAM recommended
> **Platform:** Windows 10/11

---

## Features

- 🎙️ **High-Quality TTS** - Qwen2-TTS models (0.6B/1.7B) for natural-sounding speech
- ⚡ **GPU Accelerated** - Batch processing with CUDA support (4.6x faster than real-time)
- 📚 **Chapter Support** - Automatic chapter detection and separate audio files
- 🎵 **Multiple Voices** - 20+ pre-configured voices with emotion support
- 📊 **Real-time Monitoring** - VRAM usage, progress tracking, activity logs
- 🔧 **Easy Setup** - Portable version for non-developers or manual install for advanced users

---

## Quick Start

### For Beginners (Portable Version - Recommended)

1. **Download** this repository (Code → Download ZIP)
2. **Extract** the ZIP file
3. **Navigate** to the `VOX-1-Portable/` folder
4. **Run** `Download-Python.bat` (downloads Python 3.10)
5. **Run** `Setup-Portable.bat` (sets up everything automatically, 5-10 minutes)
6. **Launch** `Launch VOX-1 Portable.vbs`

That's it! No Python installation, no admin rights needed.

### For Developers (Manual Install)

See [MANUAL_INSTALL.md](MANUAL_INSTALL.md) for detailed setup instructions.

**Requirements:**
- Python 3.10
- NVIDIA GPU with CUDA support
- 8GB+ VRAM (12GB+ recommended)
- Windows 10/11

**Quick Install:**
```bash
# Clone the repository
git clone https://github.com/marcusau2/VOX-1-Audiobook-Maker.git
cd VOX-1-Audiobook-Maker

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
```

---

## Usage

### Basic Workflow

1. **Create/Load Voice** (The Lab tab)
   - Design voice from text description, OR
   - Clone voice from audio sample (10-30s)
   - Save as Master Voice

2. **Load Book** (BookSmith or Studio tab)
   - EPUB/PDF: Use BookSmith to extract chapters
   - TXT/JSON: Use Studio directly

3. **Render** (Studio tab)
   - Load Master Voice
   - Load Book
   - Click "Render Audiobook"
   - Output: MP3 (TXT) or M4B with chapters (EPUB/PDF/JSON)

### Recommended Settings

| GPU VRAM | Batch Size | Model Size | Expected Speed |
|----------|------------|------------|----------------|
| 8-10 GB  | 1-2        | 0.6B       | ~1.5x realtime |
| 12 GB    | 3-5        | 0.6B       | ~1.8x realtime |
| 16 GB+   | 5-10       | 1.7B       | ~2.0x realtime |

---

## Project Structure

```
VOX-1-Audiobook-Maker/
├── app.py                  # Main GUI application
├── backend.py              # TTS processing engine
├── requirements.txt        # Python dependencies
├── booksmith_module/       # Text processing utilities
├── ffmpeg_bundle/          # Audio processing tools
├── VOX-1-Portable/         # Portable version setup scripts
├── Launch Vox-1.vbs        # Quick launcher (no console)
├── Launch Vox-1.bat        # Debug launcher (shows console)
└── README.md               # This file
```

---

## Performance

**Current Benchmarks (RTX 3060 12GB):**
- Model: Qwen2-TTS 0.6B
- Batch Size: 3
- Attention: SDPA
- Speed: 16.32s per chunk (~1.8x faster than real-time)
- VRAM: ~7.2GB stable (60% utilization)

---

## Troubleshooting

### "CUDA out of memory" error
- Reduce batch size in Advanced Settings (try batch_size=1)
- Switch to 0.6B model instead of 1.7B
- Close other GPU applications

### Slow generation
- Check VRAM usage in activity log
- Increase batch size if VRAM allows
- Try different attention modes (sdpa, sage_attn, flash_attn_2)

### Voice not loading
- Check that voice JSON files exist in project root
- Verify voice name matches exactly (case-sensitive)

---

## Configuration

**Settings File:** `user_settings.json`

```json
{
  "batch_size": 3,          // Chunks processed simultaneously
  "chunk_size": 500,        // Characters per chunk
  "model_size": "0.6B",     // TTS model (0.6B or 1.7B)
  "attention_mode": "sdpa", // Attention implementation
  "temperature": 0.7,       // Voice variation (0.1-2.0)
  "repetition_penalty": 1.05
}
```

**Adjust in GUI:** Advanced Settings tab

---

## Supported Formats

| Type | Input | Output |
|------|-------|--------|
| Books | TXT, EPUB, PDF, JSON | MP3, M4B |
| Voice | WAV, MP3 | WAV (optimized) |

---

## Technical Details

### Models Used
- **Qwen2-TTS 0.6B** - Fast, efficient, great quality (default)
- **Qwen2-TTS 1.7B** - Higher quality, requires more VRAM

### Attention Mechanisms
- **SDPA** - Scaled Dot Product Attention (default, fastest)
- **sage_attn** - Memory-efficient attention
- **flash_attn_2** - Flash Attention 2 (requires installation)

### Audio Processing
- Output: MP3 format (configurable)
- Sample Rate: 24kHz
- Bitrate: 192kbps (configurable)

---

## Documentation

📄 **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Complete project overview
📄 **[MANUAL_INSTALL.md](MANUAL_INSTALL.md)** - Advanced installation guide
📄 **[PORTABLE_VERSION_GUIDE.md](PORTABLE_VERSION_GUIDE.md)** - Portable setup details
📄 **[booksmith_module/README.md](booksmith_module/README.md)** - EPUB/PDF processing

---

## Known Issues

- First generation after launch is slower (model loading)
- Very long texts (>50k words) may require multiple sessions
- Some special characters may not render correctly in audio

---

## Roadmap

- [ ] Linux support
- [ ] Voice cloning from user samples
- [ ] Real-time preview
- [ ] Multi-language support
- [ ] Cloud GPU integration
- [ ] Plugin system for custom voices

---

## License

TBD - Currently private development

---

## Credits

Built with:
- [Qwen2-TTS](https://github.com/QwenLM/Qwen2-Audio) by Alibaba
- [PyTorch](https://pytorch.org/)
- [Gradio](https://gradio.app/) for UI
- [FFmpeg](https://ffmpeg.org/) for audio processing

---

## Contact

For issues and questions, please open a GitHub issue or contact the maintainer directly.

---

**Last Updated:** January 2025
