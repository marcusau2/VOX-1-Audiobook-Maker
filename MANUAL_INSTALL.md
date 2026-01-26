# Manual Installation Guide

This guide is for developers and advanced users who want to install VOX-1 manually with full control over their environment.

---

## Prerequisites

### Required Software

1. **Python 3.10.x**
   - Download from: https://www.python.org/downloads/
   - **Important:** Python 3.10 specifically (not 3.11, 3.12)
   - During install, check "Add Python to PATH"

2. **NVIDIA GPU Drivers**
   - CUDA 12.1 or higher
   - Download from: https://www.nvidia.com/Download/index.aspx

3. **Git** (optional, for cloning)
   - Download from: https://git-scm.com/downloads

### System Requirements

- **OS:** Windows 10/11 64-bit
- **GPU:** NVIDIA with 8GB+ VRAM (12GB+ recommended)
- **RAM:** 16GB+ recommended
- **Storage:** ~10GB for dependencies and models

---

## Installation Methods

### Method 1: Git Clone (Recommended)

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/VOX-1-Audiobook-Maker.git
cd VOX-1-Audiobook-Maker

# Create virtual environment (optional but recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Method 2: Download ZIP

1. Go to the GitHub repository
2. Click "Code" → "Download ZIP"
3. Extract to your desired location
4. Open command prompt in that folder
5. Run:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## Dependencies

The `requirements.txt` includes:

- **PyTorch** (2.0+) with CUDA support
- **Transformers** (Hugging Face)
- **Gradio** (UI framework)
- **FFmpeg** (audio processing)
- **numpy, scipy** (numerical computing)
- **Qwen2-TTS** models and dependencies

Installation may take 5-10 minutes depending on internet speed.

---

## Verification

After installation, verify everything works:

```bash
# Test Python version
python --version
# Should show: Python 3.10.x

# Test CUDA availability
python -c "import torch; print(torch.cuda.is_available())"
# Should show: True

# Test GPU detection
python -c "import torch; print(torch.cuda.get_device_name(0))"
# Should show your GPU name

# Run the app
python app.py
```

---

## Running the Application

### Method 1: Command Line
```bash
python app.py
```

### Method 2: Launcher Scripts

**Windows (no console):**
```
Launch Vox-1.vbs
```

**Windows (with console for debugging):**
```
Launch Vox-1.bat
```

### Method 3: Python Launcher
```bash
py -3.10 app.py
```

---

## Configuration

### User Settings

Edit `user_settings.json` to customize defaults:

```json
{
  "batch_size": 3,
  "chunk_size": 500,
  "model_size": "0.6B",
  "attention_mode": "sdpa",
  "temperature": 0.7,
  "repetition_penalty": 1.05,
  "output_format": "mp3",
  "audio_bitrate": "192k"
}
```

### Performance Tuning

**For 8GB VRAM:**
```json
{
  "batch_size": 1,
  "model_size": "0.6B",
  "attention_mode": "sdpa"
}
```

**For 12GB VRAM:**
```json
{
  "batch_size": 3,
  "model_size": "0.6B",
  "attention_mode": "sdpa"
}
```

**For 16GB+ VRAM:**
```json
{
  "batch_size": 5,
  "model_size": "1.7B",
  "attention_mode": "sdpa"
}
```

---

## Troubleshooting

### Installation Issues

**"No matching distribution found for torch"**
- Ensure you're using Python 3.10 (not 3.11+)
- Try: `pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121`

**"CUDA not available"**
- Verify NVIDIA drivers are installed
- Check CUDA version: `nvidia-smi`
- Reinstall PyTorch with CUDA support

**"ModuleNotFoundError"**
- Activate virtual environment if using one
- Run: `pip install -r requirements.txt` again

### Runtime Issues

**"CUDA out of memory"**
- Reduce `batch_size` in user_settings.json
- Switch to `model_size: "0.6B"`
- Close other GPU applications
- Restart the app

**"Models not found"**
- First run downloads models automatically
- Check internet connection
- Models stored in: `C:\Users\YourName\.cache\huggingface\`

**Slow performance**
- Check VRAM usage in activity log
- Ensure `attention_mode: "sdpa"` (fastest)
- Increase `batch_size` if VRAM allows
- Verify GPU is being used: Activity log shows VRAM stats

---

## Development

### Project Structure

```
VOX-1-Audiobook-Maker/
├── app.py                  # Main GUI (Gradio)
├── backend.py              # TTS engine (batch processing)
├── requirements.txt        # Python dependencies
├── user_settings.json      # Configuration
├── booksmith_module/       # EPUB/PDF text extraction
│   ├── __init__.py
│   ├── core.py
│   └── processors.py
├── ffmpeg_bundle/          # Audio processing tools
├── ComfyUI-Qwen-TTS/       # TTS model integration
├── Output/                 # Generated audio files
├── VOX-Output/             # Final audiobooks
└── temp_work/              # Temporary processing files
```

### Key Files

- **app.py** - Gradio UI, event handlers
- **backend.py** - TTS generation, batch processing, VRAM monitoring
- **booksmith_module/core.py** - EPUB/PDF chapter extraction
- **user_settings.json** - Persistent configuration

### Making Changes

1. Edit source files as needed
2. Test changes: `python app.py`
3. Create new settings in GUI (Advanced Settings tab)
4. Check activity log for debugging info

---

## Building Executables

If you want to create a standalone executable:

```bash
python build.py
```

Output will be in `dist/Vox-1/Vox-1.exe`

---

## Updating

### Git Method
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Manual Method
1. Download latest ZIP from GitHub
2. Extract to new folder
3. Copy your `user_settings.json` from old folder
4. Run: `pip install -r requirements.txt --upgrade`

---

## Uninstallation

### With Virtual Environment
```bash
# Delete the entire project folder
# Virtual environment is self-contained
```

### System-wide Installation
```bash
# Uninstall packages
pip uninstall -r requirements.txt -y

# Delete project folder
# Models remain in: C:\Users\YourName\.cache\huggingface\
```

---

## Advanced Configuration

### Custom Voice Files

Place custom voice JSON files in project root:

```json
{
  "speaker": "path/to/audio/reference.wav",
  "emotion": {
    "happy": 0.5,
    "sad": 0.1,
    "angry": 0.0,
    "surprised": 0.2,
    "fearful": 0.0,
    "disgusted": 0.0
  }
}
```

### Custom Models

To use custom Qwen2-TTS models:

1. Place model in: `models/your-custom-model/`
2. Update backend.py model path
3. Restart app

---

## Getting Help

- Check [README.md](README.md) for basic info
- See [PROJECT_STATUS.md](PROJECT_STATUS.md) for current status
- Open GitHub issue for bugs/feature requests
- Check activity log for detailed error messages

---

## Performance Tips

1. **First run is slow** - Models download and load (one-time)
2. **Batch processing** - Higher batch size = faster (if VRAM allows)
3. **Model size** - 0.6B is faster, 1.7B is higher quality
4. **Attention mode** - sdpa is fastest, flash_attn_2 may be faster if installed
5. **Close other apps** - Free up VRAM for better performance

---

**Last Updated:** January 2025
