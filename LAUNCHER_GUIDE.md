# VOX-1 Launcher Guide

## Quick Start

Double-click **`Launch Vox-1.vbs`** to start the app (no console window).

---

## Launcher Options

### Option 1: Launch Vox-1.vbs (Recommended)
**Best user experience:**
- Double-click to launch
- No console window visible
- Clean startup
- GUI appears directly

**How it works:**
- VBScript finds Python 3.10 automatically
- Launches app.py in hidden mode
- Shows error message if Python 3.10 not found

---

### Option 2: Launch Vox-1.bat
**For debugging:**
- Double-click to launch
- Shows brief console message
- Console closes automatically after launch
- Useful if you need to see startup errors

**How it works:**
- Batch file checks for Python 3.10
- Launches app.py
- Console window closes after GUI starts

---

## Requirements

**Python 3.10.8 must be installed:**
- Download from: https://www.python.org/downloads/release/python-3108/
- During installation, check "Add Python to PATH"
- Install pip and py launcher

**Dependencies installed:**
```bash
cd "E:\Gemini Projects\Audiobook Maker"
py -3.10 -m pip install -r requirements.txt
```

---

## Troubleshooting

### "Python 3.10 is not installed or not found"
**Solution:**
1. Install Python 3.10.8 from the link above
2. Make sure "Add to PATH" was checked during install
3. Restart computer
4. Try launching again

### GUI doesn't appear
**Solution:**
1. Use `Launch Vox-1.bat` to see error messages
2. Check if dependencies are installed:
   ```bash
   py -3.10 -m pip install -r requirements.txt
   ```
3. Check Activity Log in temp folder if app crashes

### Module errors (qwen_tts, torch, etc.)
**Solution:**
```bash
cd "E:\Gemini Projects\Audiobook Maker"
py -3.10 -m pip install -r requirements.txt --upgrade
```

---

## Creating Desktop Shortcut

**For Launch Vox-1.vbs:**
1. Right-click `Launch Vox-1.vbs`
2. Select "Create shortcut"
3. Drag shortcut to Desktop
4. Rename to "VOX-1 Audiobook Generator"

**Optional - Custom icon:**
1. Right-click shortcut → Properties
2. Click "Change Icon"
3. Browse to an .ico file or use system icons

---

## Portable Version (Coming Soon)

Portable version will include:
- Bundled Python 3.10
- All dependencies pre-installed
- Self-contained folder
- No installation required
- Just copy folder and run

---

## Technical Details

**Launch Vox-1.vbs:**
- Uses Windows Script Host (VBScript)
- Runs Python with `py -3.10 app.py`
- Window style = 0 (hidden)
- Async launch (doesn't wait for app to close)

**Launch Vox-1.bat:**
- Standard Windows batch file
- Checks Python availability first
- Shows error message if Python missing
- Launches with `start /B` (background)

**Both launchers:**
- Auto-detect project directory
- Change to correct working directory
- Find Python 3.10 using py launcher
- Show user-friendly error if Python missing
