# VOX-1 Portable Version Guide

## Overview

The portable version includes Python + dependencies bundled together, allowing the app to run on any Windows PC without installation.

---

## Setup Process

### Step 1: Download Python
```
Double-click: VOX-1-Portable\Download-Python.bat
```

**What it does:**
- Downloads Python 3.10.11 Embedded (8.9 MB)
- Extracts to `python310/` folder
- Takes ~1 minute

### Step 2: Setup Application
```
Double-click: VOX-1-Portable\Setup-Portable.bat
```

**What it does:**
1. Configures embedded Python to allow pip
2. Installs pip package manager
3. Copies all application files to `app/` folder
4. Installs dependencies (PyTorch, qwen-tts, etc.)
5. Creates output directories

**Time required:** 5-10 minutes (downloads ~4GB of dependencies)

### Step 3: Launch
```
Double-click: VOX-1-Portable\Launch VOX-1 Portable.vbs
```

**Result:** GUI opens, fully functional!

---

## Folder Structure

```
VOX-1-Portable/
├── python310/                      # Embedded Python 3.10
│   ├── python.exe
│   ├── python310.dll
│   ├── Lib/
│   │   └── site-packages/         # Dependencies installed here
│   └── Scripts/
│       └── pip.exe
│
├── app/                            # Application files
│   ├── app.py                     # Main GUI
│   ├── backend.py                 # Audio engine
│   ├── booksmith_module/          # EPUB/PDF processing
│   ├── ffmpeg_bundle/             # Audio tools
│   ├── requirements.txt           # Dependencies list
│   ├── user_settings.json         # User preferences
│   ├── Output/                    # Generated audiobooks
│   ├── VOX-Output/               # Optimized voice files
│   └── temp_work/                # Render cache
│
├── Download-Python.bat            # Step 1: Get Python
├── Setup-Portable.bat             # Step 2: Setup
├── Launch VOX-1 Portable.vbs     # Step 3: Launch app
├── SETUP_INSTRUCTIONS.txt        # Quick guide
└── README.txt                    # User manual
```

---

## Technical Details

### Embedded Python Configuration

**python310._pth file:**
```
python310.zip
.
..
import site
```

**Why this matters:**
- Enables pip in embedded Python
- Allows installing packages locally
- Keeps everything self-contained

### Dependency Installation

Dependencies installed to: `python310\Lib\site-packages\`

**Major packages:**
- PyTorch 2.7.1 (~2GB)
- qwen-tts
- transformers
- whisper
- customtkinter
- And 50+ dependencies

**Total size after setup:** ~4-5GB

### Launcher Operation

**Launch VOX-1 Portable.vbs does:**
1. Check if `python310\python.exe` exists
2. Check if `app\app.py` exists
3. Change directory to `app/`
4. Run: `python310\python.exe app\app.py` (hidden window)
5. Exit (GUI runs independently)

---

## Advantages

✅ **No installation** - Just download and setup
✅ **No admin rights** - Runs from any folder
✅ **Fully portable** - Copy folder to USB/network drive
✅ **Self-contained** - All dependencies included
✅ **No conflicts** - Doesn't touch system Python
✅ **Clean uninstall** - Just delete folder

---

## Size Breakdown

| Component | Size |
|-----------|------|
| Embedded Python | 9 MB |
| Application files | 500 KB |
| Dependencies (PyTorch, etc.) | 4-5 GB |
| **Total** | **~5 GB** |

**Note:** Models downloaded on first use (~1.5GB more)

---

## Distribution

### Sharing with Others

**Option 1: Full Package**
- Zip entire VOX-1-Portable folder after setup
- Share 5GB zip file
- Recipients just unzip and run launcher
- No setup needed for them

**Option 2: Setup Package**
- Share VOX-1-Portable folder before setup (~1 MB)
- Recipients run Download-Python.bat + Setup-Portable.bat
- Requires internet connection on their end

### Creating Distribution Package

```bash
# After setup completes on your machine:
cd "E:\Gemini Projects\Audiobook Maker"
tar -czf VOX-1-Portable.tar.gz VOX-1-Portable/

# Or use 7-Zip:
# Right-click VOX-1-Portable → 7-Zip → Add to archive
# Format: ZIP or 7z (better compression)
```

---

## Updating

### Update Application Code
1. Edit files in `VOX-1-Portable\app\`
2. Launch as normal
3. Changes take effect immediately

### Update Dependencies
```bash
cd VOX-1-Portable
python310\python.exe -m pip install -r app\requirements.txt --upgrade
```

### Update Python (major version)
- Not recommended - would break compatibility
- Stick with Python 3.10 for stability

---

## Troubleshooting

### "Python 3.10 not found"
**Solution:**
- Run Download-Python.bat
- Or download manually from: https://www.python.org/ftp/python/3.10.11/
- Extract to `python310/` folder

### "Setup failed - pip install errors"
**Common causes:**
1. No internet connection
2. Firewall blocking downloads
3. Disk space full

**Solution:**
- Check internet
- Temporarily disable firewall
- Free up disk space (need 8GB)
- Run Setup-Portable.bat again

### "Module not found" when launching
**Solution:**
- Setup didn't complete properly
- Run Setup-Portable.bat again
- Check that `python310\Lib\site-packages\` has packages

### GUI doesn't appear
**Solution:**
1. Check Task Manager - python.exe running?
2. Check `app\` folder exists with files
3. Run Setup-Portable.bat again
4. Check antivirus - may be blocking

### Out of memory during render
**Solution:**
- Same as non-portable version
- Reduce batch size in Advanced Settings
- Close other GPU apps

---

## Comparison: Portable vs Installed

| Feature | Portable | Installed (Launcher) |
|---------|----------|---------------------|
| Installation | Setup script (10 min) | pip install (5 min) |
| Admin rights | Not required | Not required |
| Size on disk | 5 GB | 4 GB |
| Update app | Replace files | Replace files |
| Update Python | Reinstall | System update |
| Share with others | Copy folder | Need Python 3.10 |
| Conflicts | None | Possible with system Python |

**Recommendation:**
- **Portable:** For sharing, multiple PCs, clean systems
- **Installed:** For development, easier updates

---

## Security Notes

### What's Downloaded
- Python 3.10.11 from python.org (official)
- Packages from PyPI (official Python package index)
- All via HTTPS

### What's Included
- No executables besides python.exe
- No modified binaries
- Pure Python application
- Open source dependencies

### Antivirus
Some antivirus may flag:
- `python.exe` (false positive)
- PyTorch CUDA files (false positive)

**Solution:** Add VOX-1-Portable folder to antivirus exceptions

---

## Performance

**Same as installed version:**
- 16s per chunk (batch size 3)
- 2x faster than real-time
- GPU VRAM monitoring
- All optimizations included

**No performance penalty** from using embedded Python.

---

## Next Steps

After setup completes:
1. Double-click launcher to open GUI
2. Go to "The Lab" tab to create/load voice
3. Go to "BookSmith" or "Studio" to render book
4. Check "Advanced Settings" for optimal batch size

See `app\README.md` for full usage guide.

---

## Support

For issues:
1. Check `app\PROJECT_STATUS.md` for troubleshooting
2. Review setup logs (console output)
3. Try running Setup-Portable.bat again

---

**The portable version is now ready to use and distribute!**
