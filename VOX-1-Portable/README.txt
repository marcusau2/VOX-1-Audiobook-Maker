==========================================
VOX-1 AUDIOBOOK GENERATOR - PORTABLE
==========================================

Version: Portable (Launcher-based)
Last Updated: 2025-01-25

==========================================
QUICK START
==========================================

FIRST TIME SETUP:
1. Double-click: Download-Python.bat
2. Wait for download to complete
3. Double-click: Setup-Portable.bat
4. Wait 5-10 minutes for setup

DAILY USE:
- Double-click: Launch VOX-1 Portable.vbs

That's it!

==========================================
WHAT IS THIS?
==========================================

VOX-1 converts books (TXT, EPUB, PDF) into
AI-narrated audiobooks using voice cloning.

Features:
- Create custom voices from descriptions
- Clone voices from audio samples
- Process entire books with chapters
- Generate MP3 or M4B audiobooks
- Fast batch processing (16s per chunk)

==========================================
SYSTEM REQUIREMENTS
==========================================

- Windows 10/11 (64-bit)
- NVIDIA GPU with 6GB+ VRAM (12GB recommended)
- 8GB disk space for portable version
- Internet for initial setup only

==========================================
PORTABILITY
==========================================

This version is FULLY PORTABLE:
- No installation required
- No admin rights needed
- Copy folder to any Windows PC
- Includes Python + all dependencies

Just copy the entire VOX-1-Portable folder!

==========================================
FOLDER STRUCTURE
==========================================

VOX-1-Portable/
├── python310/               [Embedded Python]
├── app/                     [Application files]
│   ├── Output/             [Generated audiobooks]
│   ├── VOX-Output/         [Optimized voice files]
│   ├── temp_work/          [Render cache]
│   └── ...
├── Download-Python.bat      [Setup step 1]
├── Setup-Portable.bat       [Setup step 2]
├── Launch VOX-1 Portable.vbs [Main launcher]
└── README.txt              [This file]

==========================================
PERFORMANCE
==========================================

Default settings (optimized):
- Batch size: 3 (safe for 12GB VRAM)
- Model: 0.6B (fast rendering)
- Attention: sdpa (reliable)

Speed: ~16 seconds per chunk
Result: ~2x faster than real-time

Adjust batch size in Advanced Settings if needed:
- 24GB GPU: Try batch 10
- 16GB GPU: Try batch 5
- 12GB GPU: Use batch 3 (default)
- 8GB GPU: Use batch 2

==========================================
DOCUMENTATION
==========================================

After setup, see:
- app/README.md - Full documentation
- app/PROJECT_STATUS.md - Technical details
- app/LAUNCHER_GUIDE.md - Launcher info

==========================================
TROUBLESHOOTING
==========================================

Setup fails:
- Check internet connection
- Run Setup-Portable.bat again
- May need to install Visual C++ Redistributable

App won't launch:
- Make sure setup completed successfully
- Check python310/python.exe exists
- Check app/app.py exists

Out of memory during render:
- Reduce batch size to 2 or 1
- Close other GPU applications
- Use 0.6B model (default)

==========================================
SUPPORT
==========================================

For issues or questions:
- Check app/PROJECT_STATUS.md
- See troubleshooting section above
- Review activity logs in app folder

==========================================
LICENSE
==========================================

MIT License - See app/LICENSE for details

==========================================

Enjoy creating audiobooks with VOX-1!
