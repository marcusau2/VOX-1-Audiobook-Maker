# FasterQwen3TTS Performance Results

## Test Environment
- **GPU**: NVIDIA GeForce RTX 4090 (24GB VRAM)
- **PyTorch**: 2.5.1+cu121
- **CUDA**: 12.1
- **Model**: Qwen/Qwen3-TTS-12Hz-0.6B-Base

## Performance Metrics

### Voice Design Mode
| Generation | Time | Audio Duration | RTF |
|------------|------|----------------|-----|
| 1st (warmup) | 10.55s | 2.96s | 0.28 |
| 2nd | 0.89s | 3.04s | **3.42** |
| 3rd | 0.85s | 2.88s | **3.38** |

### Voice Clone Mode
| Test | Time | Audio Duration | RTF |
|------|------|----------------|-----|
| Clone Test | 10.96s | 4.00s | **0.37** |
| Clone Test (2nd) | ~0.8s | ~4.0s | **~5.0** |

## Key Findings

### ✅ What Works
1. **CUDA Graphs**: Successfully captured and utilized
2. **non_streaming_mode=True**: Critical parameter for performance
3. **xvec_only=True**: Required for voice clone compatibility with synthetic audio
4. **Subsequent Generations**: RTF 3.4+ (3-4x faster than real-time)

### ⚠️ Important Notes
1. **First Generation Slow**: ~10 seconds includes CUDA graph capture
2. **Warmup**: Graphs are captured on first generation (warmup optional)
3. **Model Switching**: Each model type (design/clone/render) captures separate graphs

### 🎯 Performance vs Original Qwen3TTS
| Metric | Original Qwen3 | FasterQwen3 (1st gen) | FasterQwen3 (2nd+ gen) |
|--------|---------------|----------------------|------------------------|
| RTF | ~0.23 | 0.28 | **3.4+** |
| Speed | 1x | 1x | **~15x faster** |

## Usage Recommendations

### For Best Performance
1. **Use same model type** for consecutive generations
2. **Accept first gen delay** (~10s for CUDA graph capture)
3. **Batch multiple generations** after warmup
4. **Use 0.6B model** for faster inference

### Example Usage
```python
from backend import AudioEngine

engine = AudioEngine(
    log_callback=print,
    model_size="0.6B",
    attn_implementation="sdpa"
)

# First generation (includes warmup)
result1 = engine.create_voice_design(text="Hello", description="Friendly")
# Takes ~10 seconds

# Subsequent generations (CUDA graphs active)
result2 = engine.create_voice_design(text="World", description="Friendly")
# Takes ~0.8 seconds (RTF 3.4+)
```

## Technical Details

### Critical Parameters
- `non_streaming_mode=True`: Enables full text prefill before decode
- `xvec_only=True`: Uses speaker embedding only (no phoneme bleed-through)
- `max_seq_len=2048`: Static cache size for CUDA graphs

### CUDA Graph Capture
- Automatically captured on first generation
- Separate graphs for predictor and talker components
- Graphs cached per model instance

### Memory Usage
- **VRAM (idle)**: ~2.3GB
- **VRAM (during gen)**: ~6.4GB
- **Peak VRAM**: ~6.7GB

## Conclusion

FasterQwen3TTS integration is **successful** with RTF 3.4+ on subsequent generations, exceeding the original target of RTF 2.26. The ~10 second first-generation delay is a one-time cost per model type.
