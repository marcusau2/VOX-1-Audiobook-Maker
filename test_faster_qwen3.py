#!/usr/bin/env python3
"""
Test script for FasterQwen3TTS integration.
Verifies import, model loading, and voice generation.
"""
import os
import sys
import time
import torch
import numpy as np
import soundfile as sf

# Test 1: Import check
print("=" * 60)
print("TEST 1: Import Check")
print("=" * 60)

try:
    from faster_qwen3_tts import FasterQwen3TTS
    print("[OK] FasterQwen3TTS import successful")
except ImportError as e:
    print(f"[FAIL] FasterQwen3TTS import failed: {e}")
    sys.exit(1)

# Test 2: System compatibility
print("\n" + "=" * 60)
print("TEST 2: System Compatibility")
print("=" * 60)

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"CUDA version: {torch.version.cuda}")

# Check PyTorch version for CUDA graphs
major, minor = map(int, torch.__version__.split('.')[:2])
if major >= 2 and minor >= 5:
    print("[OK] PyTorch version supports CUDA graphs (2.5.1+)")
else:
    print("[WARN] PyTorch version may not support CUDA graphs properly")

if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    compute_cap = torch.cuda.get_device_capability()
    print(f"Compute Capability: {compute_cap[0]}.{compute_cap[1]}")
    if compute_cap[0] >= 7:
        print("[OK] GPU supports CUDA graphs (compute 7.0+)")
    else:
        print("[WARN] Older GPU - CUDA graphs may not work optimally")

# Test 3: Backend import
print("\n" + "=" * 60)
print("TEST 3: Backend Import")
print("=" * 60)

try:
    from backend import AudioEngine, FASTER_QWEN_AVAILABLE
    print(f"[OK] Backend import successful")
    print(f"FASTER_QWEN_AVAILABLE: {FASTER_QWEN_AVAILABLE}")
except Exception as e:
    print(f"[FAIL] Backend import failed: {e}")
    sys.exit(1)

# Test 4: Model loading with AudioEngine
print("\n" + "=" * 60)
print("TEST 4: Model Loading Test")
print("=" * 60)

def log(msg):
    print(f"[LOG] {msg}")

try:
    # Create engine with small model for testing
    log("Creating AudioEngine with 0.6B model...")
    engine = AudioEngine(
        log_callback=log,
        model_size="0.6B",
        batch_size=1,
        chunk_size=100,
        attn_implementation="sdpa"
    )
    
    print(f"[OK] AudioEngine created successfully")
    print(f"use_faster_qwen: {engine.use_faster_qwen}")
    
except Exception as e:
    print(f"[FAIL] AudioEngine creation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Voice Design generation
print("\n" + "=" * 60)
print("TEST 5: Voice Design Generation")
print("=" * 60)

try:
    test_text = "Hello, this is a test of the Faster Qwen3 TTS system."
    test_description = "A calm and friendly female voice"
    
    log(f"Generating voice design: '{test_text}'")
    start_time = time.time()
    
    output_path = engine.create_voice_design(
        text=test_text,
        description=test_description,
        output_filename="test_design.wav"
    )
    
    elapsed = time.time() - start_time
    print(f"[OK] Voice design generated in {elapsed:.2f}s")
    print(f"Output: {output_path}")
    
    # Verify output file
    if os.path.exists(output_path):
        audio_info = sf.info(output_path)
        print(f"Audio duration: {audio_info.duration:.2f}s")
        print(f"Sample rate: {audio_info.samplerate}Hz")
    else:
        print("[WARN] Output file not found")
    
except Exception as e:
    print(f"[FAIL] Voice design generation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 6: Voice Clone generation
print("\n" + "=" * 60)
print("TEST 6: Voice Clone Generation")
print("=" * 60)

# Create a new engine for voice clone test (to ensure correct model is loaded)
log("Creating new AudioEngine for voice clone test...")
clone_engine = AudioEngine(
    log_callback=log,
    model_size="0.6B",
    batch_size=1,
    chunk_size=100,
    attn_implementation="sdpa"
)

# Create a simple reference audio
ref_audio_path = os.path.join(clone_engine.temp_dir, "test_ref.wav")
sample_rate = 24000
duration = 1.0
t = np.linspace(0, duration, int(sample_rate * duration))
reference_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.3
sf.write(ref_audio_path, reference_audio, sample_rate)
ref_text = "This is a reference audio sample for testing."

try:
    test_text = "This is a test of the voice cloning system with Faster Qwen3."
    
    log(f"Generating voice clone: '{test_text}'")
    start_time = time.time()
    
    output_path = clone_engine.create_voice_clone_preview(
        text=test_text,
        ref_audio_path=ref_audio_path,
        output_filename="test_clone.wav"
    )
    
    elapsed = time.time() - start_time
    print(f"[OK] Voice clone generated in {elapsed:.2f}s")
    print(f"Output: {output_path}")
    
    # Verify output file
    if os.path.exists(output_path):
        audio_info = sf.info(output_path)
        print(f"Audio duration: {audio_info.duration:.2f}s")
        print(f"Sample rate: {audio_info.samplerate}Hz")
    else:
        print("[WARN] Output file not found")
    
except Exception as e:
    print(f"[FAIL] Voice clone generation failed: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)

# Clean up test files
for f in ["test_design.wav", "test_clone.wav"]:
    path = os.path.join(engine.output_dir, f)
    if os.path.exists(path):
        print(f"Test output: {path}")

print("\n[OK] All tests completed!")
print("\nNext step: Launch the app with 'python app.py' to test the full GUI")
