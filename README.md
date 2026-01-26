# VOX-1 Audiobook Maker

GPU-accelerated audiobook generator using Qwen2-TTS models. Create professional-quality audiobooks with natural-sounding speech, batch processing, and automatic chapter management.

---

## 🚀 Quick Install (Recommended)

### Step 1: Create Project Folder
Create a folder where you want VOX-1 installed. For example:
- `C:\VOX-1\`
- `D:\Projects\VOX-1\`
- Or anywhere you prefer

### Step 2: Download Installer
Download the installer script:
**[Install-VOX-1.bat](https://raw.githubusercontent.com/marcusau2/VOX-1-Audiobook-Maker/main/Install-VOX-1.bat)**

Right-click the link → "Save link as..." → Save to your project folder

### Step 3: Run Installer
1. Go to your project folder
2. Double-click `Install-VOX-1.bat`
3. Wait 10-15 minutes while it downloads everything (~2.5 GB)

### Step 4: Launch
After installation completes:
1. `START_HERE.txt` will open automatically with instructions
2. Double-click `RUN-VOX-1.bat` to start the app
3. Read `USER_GUIDE.txt` for complete instructions

That's it! The app will open in your browser.

---

## 📦 What Gets Installed

The installer automatically downloads and sets up:
- ✅ Python 3.10 (embedded, no system install needed)
- ✅ VOX-1 source code
- ✅ FFmpeg (audio processing, from GitHub)
- ✅ PyTorch + CUDA (~2 GB)
- ✅ All Python dependencies

**Installation size:** ~2.7 GB
**Installation time:** 10-15 minutes

### First Run - Additional Downloads

The first time you use each feature, AI models download automatically:
- **Voice Design:** ~3.4 GB (one-time)
- **Voice Cloning:** ~3.4 GB (one-time)
- **Audiobook Generation:** ~1.2 GB (one-time)

**Total storage needed:** ~8-10 GB
**Models cache to:** `C:\Users\YourName\.cache\huggingface\`
**After first run:** Everything loads instantly from cache!

---

## 💻 System Requirements

- **OS:** Windows 10/11 64-bit
- **GPU:** NVIDIA with 8GB+ VRAM (12GB recommended)
- **CUDA:** Automatically installed with PyTorch
- **Storage:** ~5 GB free space
- **Internet:** Required for installation only

---

## 🎯 Features

- 🎙️ **High-Quality TTS** - Qwen2-TTS models (0.6B/1.7B)
- ⚡ **GPU Accelerated** - 1.8x faster than real-time
- 📚 **Chapter Support** - Automatic chapter detection
- 🎵 **Voice Cloning** - Create custom voices
- 📊 **VRAM Monitoring** - Real-time GPU usage tracking
- 🔄 **Batch Processing** - Process multiple chunks simultaneously

---

## 📖 Usage

### Basic Workflow

1. **The Lab Tab** - Create or clone voices
   - Design voice from text description, or
   - Clone from audio sample (10-30s WAV/MP3)
   - Save as Master Voice

2. **BookSmith Tab** - Extract chapters from EPUB/PDF
   - Load EPUB or PDF file
   - Automatically extracts chapters
   - Exports as JSON

3. **Studio Tab** - Generate audiobook
   - Load Master Voice
   - Load book (TXT/JSON)
   - Click "Render Audiobook"
   - Output: MP3 or M4B with chapters

### Performance Settings

Adjust in **Advanced Settings** tab:

| GPU VRAM | Batch Size | Model Size | Speed |
|----------|------------|------------|-------|
| 8-10 GB  | 1-2        | 0.6B       | 1.5x  |
| 12 GB    | 3-5        | 0.6B       | 1.8x  |
| 16 GB+   | 5-10       | 1.7B       | 2.0x  |

---

## 📁 Folder Structure After Install

```
Your-Project-Folder/
├── RUN-VOX-1.bat              # ⭐ DOUBLE-CLICK THIS TO START
├── START_HERE.txt             # Quick start guide (opens after install)
├── USER_GUIDE.txt             # Complete user manual
├── Launch-Debug.bat           # For troubleshooting
├── Install-VOX-1.bat          # Installer (can run again to update)
├── python310/                 # Python environment
├── app/                       # VOX-1 application
│   ├── app.py                 # Main GUI
│   ├── backend.py             # TTS engine
│   ├── booksmith_module/      # Text processing
│   ├── ComfyUI-Qwen-TTS/      # TTS library
│   ├── ffmpeg_bundle/         # Audio tools
│   ├── Output/                # Generated audio
│   └── VOX-Output/            # Final audiobooks (YOUR FINISHED BOOKS HERE!)
```

---

## 🔧 Troubleshooting

### "CUDA out of memory"
- Reduce batch size in Advanced Settings
- Switch to 0.6B model instead of 1.7B
- Close other GPU applications
- Restart the app

### Slow generation
- Check VRAM usage in activity log
- Increase batch size if VRAM allows
- Try attention mode: "sdpa" (fastest)

### App won't start
- Make sure you have an NVIDIA GPU
- Check GPU drivers are updated
- Run `Launch-VOX-1-Debug.bat` to see error messages

### Installation failed
- Check internet connection
- Run installer again (it will resume)
- Manually download Python from: https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip

---

## 🔄 Updating VOX-1

To update to the latest version:
1. Run `Install-VOX-1.bat` again
2. Choose "Yes" when asked to re-download
3. Your settings and output files are preserved

---

## 🛠️ Advanced Installation (Developers)

If you want to modify the code or contribute:

```bash
# Clone repository
git clone https://github.com/marcusau2/VOX-1-Audiobook-Maker.git
cd VOX-1-Audiobook-Maker

# Install dependencies
pip install -r requirements.txt

# Run app
python app.py
```

See [MANUAL_INSTALL.md](MANUAL_INSTALL.md) for detailed instructions.

---

## 📚 Documentation

- **README.md** - This file (quick start)
- **MANUAL_INSTALL.md** - Advanced installation guide
- **booksmith_module/README.md** - Text processing details

---

## 🐛 Known Issues

- First generation after launch is slower (model loading)
- Very long texts (>50k words) may need multiple sessions
- Some special characters may not render in audio

---

## 🗺️ Roadmap

- [ ] Linux support
- [ ] Real-time preview
- [ ] Multi-language support
- [ ] Cloud GPU integration
- [ ] Plugin system for custom voices

---

## 📄 License

TBD - Currently in development

---

## 🙏 Credits

Built with:
- [Qwen2-TTS](https://github.com/QwenLM/Qwen2-Audio) by Alibaba
- [PyTorch](https://pytorch.org/)
- [Gradio](https://gradio.app/)
- [FFmpeg](https://ffmpeg.org/)

---

## 💬 Support

For issues, questions, or feature requests:
- Open an issue on GitHub
- Check existing issues for solutions

---

**Last Updated:** January 2026
