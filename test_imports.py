#!/usr/bin/env python3
"""Quick test to verify all required modules can be imported."""

import sys

def test_imports():
    """Test that all required modules can be imported."""
    modules_to_test = [
        'customtkinter',
        'qwen_tts',
        'torch',
        'torchaudio',
        'soundfile',
        'pydub',
        'whisper',
        'transformers',
        'accelerate',
        'ebooklib',
        'bs4',  # beautifulsoup4
        'numpy',
    ]

    failed = []
    passed = []

    for module in modules_to_test:
        try:
            __import__(module)
            passed.append(module)
            print(f"[OK] {module}")
        except Exception as e:
            failed.append((module, str(e)))
            print(f"[FAIL] {module}: {e}")

    print(f"\n{'='*50}")
    print(f"Passed: {len(passed)}/{len(modules_to_test)}")
    print(f"Failed: {len(failed)}/{len(modules_to_test)}")

    if failed:
        print(f"\nFailed modules:")
        for module, error in failed:
            print(f"  - {module}: {error}")
        sys.exit(1)
    else:
        print("\n[SUCCESS] All modules imported successfully!")
        sys.exit(0)

if __name__ == "__main__":
    test_imports()
