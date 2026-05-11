#!/usr/bin/env python3
"""
Performance test for FasterQwen3TTS.
Tests multiple generations to measure CUDA graph speedup.
"""
import os
import sys
import time
import torch
import numpy as np
import soundfile as sf
from backend import AudioEngine

def log(msg):
    print(f"[LOG] {msg}")

print("=" * 60)
print("FASTER QWEN3 TTS PERFORMANCE TEST")
print("=" * 60)

# Create engine
log("Creating AudioEngine...")
engine = AudioEngine(
    log_callback=log,
    model_size="0.6B",
    batch_size=1,
    chunk_size=100,
    attn_implementation="sdpa"
)

print(f"\nuse_faster_qwen: {engine.use_faster_qwen}")

# Test text
test_text = "The quick brown fox jumps over the lazy dog."
test_description = "A calm and friendly voice"

# Run multiple generations to test CUDA graph performance
print("\n" + "=" * 60)
print("RUNNING MULTIPLE GENERATIONS")
print("=" * 60)

for i in range(3):
    log(f"\n--- Generation {i+1} ---")
    start = time.time()
    
    output_path = engine.create_voice_design(
        text=test_text,
        description=test_description,
        output_filename=f"test_gen_{i}.wav"
    )
    
    elapsed = time.time() - start
    
    # Get audio duration
    audio_info = sf.info(output_path)
    duration = audio_info.duration
    
    rtf = duration / elapsed
    print(f"Generation {i+1}: {elapsed:.2f}s (audio: {duration:.2f}s, RTF: {rtf:.2f})")

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)
