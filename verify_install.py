#!/usr/bin/env python3
"""
Installation Verification Script for VOX-1 Audiobook Maker.
Checks if all required components are properly installed.
"""
import sys
import os

def check_mark(passed):
    return "[OK]" if passed else "[FAIL]"

def check_status(passed):
    return "PASS" if passed else "FAIL"

print("=" * 60)
print("VOX-1 Installation Verification")
print("=" * 60)
print()

all_passed = True

# Check 1: Python version
print(f"[1/6] Python Version... ", end="")
try:
    version = sys.version
    major = sys.version_info.major
    minor = sys.version_info.minor
    
    if major >= 3 and minor >= 10:
        print(f"{check_mark(True)} {check_status(True)} (Python {major}.{minor})")
    else:
        print(f"{check_mark(False)} {check_status(False)} (Python {major}.{minor}, requires 3.10+)")
        all_passed = False
except Exception as e:
    print(f"{check_mark(False)} {check_status(False)} ({e})")
    all_passed = False

# Check 2: PyTorch
print(f"[2/6] PyTorch... ", end="")
try:
    import torch
    print(f"{check_mark(True)} {check_status(True)} (v{torch.__version__})")
    
    # Check CUDA
    cuda_available = torch.cuda.is_available()
    print(f"      - CUDA Available: {check_mark(cuda_available)} {check_status(cuda_available)}")
    
    if cuda_available:
        print(f"      - CUDA Version: {torch.version.cuda}")
        print(f"      - GPU: {torch.cuda.get_device_name(0)}")
        
        # Check PyTorch version for CUDA graphs
        major, minor = map(int, torch.__version__.split('.')[:2])
        cuda_graphs_supported = major >= 2 and minor >= 5
        print(f"      - CUDA Graphs Support: {check_mark(cuda_graphs_supported)} {check_status(cuda_graphs_supported)}")
        
except ImportError:
    print(f"{check_mark(False)} {check_status(False)} (Not installed)")
    all_passed = False
except Exception as e:
    print(f"{check_mark(False)} {check_status(False)} ({e})")
    all_passed = False

# Check 3: FasterQwen3TTS
print(f"[3/6] FasterQwen3TTS... ", end="")
try:
    import faster_qwen3_tts
    print(f"{check_mark(True)} {check_status(True)} (v0.2.6+)")
except ImportError:
    print(f"{check_mark(False)} {check_status(False)} (Not installed)")
    all_passed = False

# Check 4: Qwen-TTS
print(f"[4/6] Qwen-TTS... ", end="")
try:
    import qwen_tts
    print(f"{check_mark(True)} {check_status(True)}")
except ImportError:
    print(f"{check_mark(False)} {check_status(False)} (Not installed)")
    all_passed = False

# Check 5: Backend
print(f"[5/6] Backend Module... ", end="")
try:
    from backend import AudioEngine, FASTER_QWEN_AVAILABLE
    print(f"{check_mark(True)} {check_status(True)}")
    print(f"      - FasterQwen Available: {check_mark(FASTER_QWEN_AVAILABLE)} {check_status(FASTER_QWEN_AVAILABLE)}")
except Exception as e:
    print(f"{check_mark(False)} {check_status(False)} ({e})")
    all_passed = False

# Check 6: FFmpeg
print(f"[6/6] FFmpeg... ", end="")
import subprocess
try:
    # Check system ffmpeg first
    result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
    if result.returncode == 0:
        print(f"{check_mark(True)} {check_status(True)} (System)")
    else:
        # Check bundled ffmpeg
        bundled_ffmpeg = os.path.join(os.path.dirname(__file__), 'ffmpeg_bundle', 'ffmpeg.exe')
        if os.path.exists(bundled_ffmpeg):
            print(f"{check_mark(True)} {check_status(True)} (Bundled)")
        else:
            print(f"{check_mark(False)} {check_status(False)} (Not found)")
            all_passed = False
except Exception as e:
    # Check bundled ffmpeg as fallback
    bundled_ffmpeg = os.path.join(os.path.dirname(__file__), 'ffmpeg_bundle', 'ffmpeg.exe')
    if os.path.exists(bundled_ffmpeg):
        print(f"{check_mark(True)} {check_status(True)} (Bundled)")
    else:
        print(f"{check_mark(False)} {check_status(False)} ({e})")
        all_passed = False

# Summary
print()
print("=" * 60)
if all_passed:
    print("[OK] All checks passed! Installation is complete.")
    print()
    print("You can now run the app with: RUN-VOX-1.bat")
else:
    print("[FAIL] Some checks failed. Please review the output above.")
    print()
    print("Troubleshooting:")
    print("  - Run the installer again: Install-VOX-1.bat")
    print("  - Check your internet connection")
    print("  - Ensure you have enough disk space")
print("=" * 60)

# Exit with appropriate code
sys.exit(0 if all_passed else 1)
