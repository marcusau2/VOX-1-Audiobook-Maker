# Batch File Launcher Implementation - 2025-01-25

## Summary

Replaced PyInstaller exe approach with simple launcher files due to dependency bundling issues.

---

## Problem with PyInstaller

**Issues encountered:**
1. Missing module: qwen_tts
2. Missing module: sox
3. Triton JIT errors (sageattention incompatible with frozen apps)
4. Complex dependency chain hard to bundle
5. 6GB+ build size

**Conclusion:** PyInstaller not suitable for complex ML apps with Triton/JIT dependencies.

---

## New Solution: Launcher Scripts

Created two launcher files that work with existing Python installation:

### 1. Launch Vox-1.vbs (Recommended)
**Features:**
- Double-click to launch
- No console window (completely hidden)
- Clean user experience
- Auto-finds Python 3.10
- Shows error popup if Python missing

**User experience:**
```
Double-click → GUI appears (no console)
```

### 2. Launch Vox-1.bat (Debug Mode)
**Features:**
- Shows brief startup message
- Console auto-closes after launch
- Useful for seeing errors
- Same Python detection

**User experience:**
```
Double-click → Brief message → Console closes → GUI appears
```

---

## How It Works

### VBS Launcher Flow
```
1. Get script directory
2. Change to project folder
3. Check if Python 3.10 exists: py -3.10 --version
4. If not found: Show error popup, exit
5. If found: Run "py -3.10 app.py" with hidden window
6. Exit launcher (GUI runs independently)
```

### Batch Launcher Flow
```
1. Change to script directory
2. Check if Python 3.10 exists
3. If not found: Show error in console, pause
4. If found: Launch app with start /B
5. Exit batch file
```

---

## Advantages Over PyInstaller

✅ **No bundling issues** - Uses installed Python environment
✅ **All dependencies work** - No frozen app limitations
✅ **Much smaller** - Just 2 small launcher files vs 6GB bundle
✅ **Easy to debug** - Can see actual Python errors
✅ **Easy to update** - Just update Python files, no rebuild
✅ **Faster development** - No 5-minute build process
✅ **No Triton/JIT issues** - Runs in normal Python interpreter

---

## User Requirements

**One-time setup:**
1. Install Python 3.10.8
2. Install dependencies: `py -3.10 -m pip install -r requirements.txt`

**Daily use:**
- Double-click `Launch Vox-1.vbs`
- That's it!

---

## Files Created

```
E:\Gemini Projects\Audiobook Maker\
├── Launch Vox-1.vbs          # Main launcher (hidden console)
├── Launch Vox-1.bat          # Debug launcher (shows console)
├── LAUNCHER_GUIDE.md         # User guide for launchers
└── BATCH_LAUNCHER_2025-01-25.md  # This file
```

---

## Next Steps: Portable Version

**Plan for portable distribution:**

1. **Create portable folder structure:**
   ```
   VOX-1-Portable/
   ├── python310/              # Embedded Python 3.10
   ├── app/                    # VOX-1 application files
   │   ├── app.py
   │   ├── backend.py
   │   ├── booksmith_module/
   │   └── ...
   ├── Launch Vox-1.vbs        # Modified to use bundled Python
   └── README.txt              # Portable usage instructions
   ```

2. **Modify launcher to use embedded Python:**
   ```vbs
   ' Instead of: py -3.10 app.py
   ' Use: python310\python.exe app\app.py
   ```

3. **Bundle dependencies:**
   - Use `pip install -r requirements.txt --target=python310\Lib\site-packages`
   - Include ffmpeg_bundle

4. **Test on clean machine:**
   - No Python installed
   - No admin rights needed
   - Just unzip and run

**Estimated portable size:** ~4-5GB (Python + dependencies + models cache)

---

## Comparison: Three Approaches

| Approach | Size | Pros | Cons |
|----------|------|------|------|
| **PyInstaller exe** | 6GB | Single exe | Dependency errors, slow builds |
| **Launcher + Installed Python** | <1MB | Simple, reliable | Requires Python install |
| **Portable (planned)** | 4-5GB | No install needed | Large download, manual updates |

**Current recommendation:** Use launcher approach (simple, works perfectly)

---

## Testing

**Test Launch Vox-1.vbs:**
1. Double-click file
2. GUI should appear with no console
3. Check defaults:
   - Model: 0.6B (Fastest)
   - Batch size: 3
   - Attention: sdpa

**Test Launch Vox-1.bat:**
1. Double-click file
2. Should see "Launching VOX-1..." message briefly
3. Console closes
4. GUI appears

**Both should:**
- Show same GUI
- Load with new optimized defaults
- Show VRAM monitoring in logs
- Work exactly like running `py -3.10 app.py`

---

## User Instructions

**For end users:**
1. Extract VOX-1 folder
2. Double-click `Launch Vox-1.vbs`
3. If error about Python:
   - Download Python 3.10.8
   - Run installer (check "Add to PATH")
   - Open command prompt
   - Run: `cd "path\to\VOX-1" && py -3.10 -m pip install -r requirements.txt`
   - Try launcher again

**For desktop shortcut:**
- Right-click `Launch Vox-1.vbs` → Create shortcut
- Move shortcut to Desktop
- Rename to "VOX-1 Audiobook Generator"

---

## Maintenance

**Updating the app:**
1. Edit Python files (app.py, backend.py, etc.)
2. No rebuild needed
3. Just launch again - changes take effect

**Updating dependencies:**
```bash
py -3.10 -m pip install -r requirements.txt --upgrade
```

**Distributing to others:**
- Share the entire folder
- Include LAUNCHER_GUIDE.md
- Users need Python 3.10 + dependencies
