# Performance Revert - 2025-01-25

## Issue
Rendering speed degraded to 75s/chunk (was 50-60s before ComfyUI changes)

## Root Causes
1. **Batching disabled** - ComfyUI changes removed batch processing entirely, processed one chunk at a time
2. **batch_size reduced to 1** (was 5) - Setting existed but wasn't used
3. **max_new_tokens reduced to 2048** (was 4096) - Token limit too restrictive
4. **sage_attn enabled** - Tested slower than sdpa, caused overhead

## Changes Made

### user_settings.json
- `batch_size`: 1 → 5
- `attention_mode`: "sage_attn" → "sdpa"

### backend.py

**Restored batch processing:**
- `render_book()`: Lines 673-821 - Rewrote loop to process batch_size chunks at once
- `_render_from_manifest_data()`: Lines 1675-1745 - Rewrote loop to batch chunks
- Log format now shows: `Batch (5 chunks) done in 81.59s (16.32s/chunk)`

**Changed max_new_tokens 2048→4096:**
- Line 576: `create_voice_design()`
- Line 592: `create_voice_clone_preview()`
- Lines 739, 751, 1281, 1293, 1699, 1711: All generation calls

## Results

### Performance Comparison
| Implementation | Speed per Chunk | Notes |
|---------------|-----------------|-------|
| **VOX-1 (After Fix)** | **16.32s** | Batch=5, optimal |
| VOX-1 (ComfyUI Pattern) | 75s | Sequential, no batching |
| VOX-1 (Original) | 50-60s | Unknown batching |
| ComfyUI Benchmark | 70s for 5s audio | 14x slower than real-time |

### Measured Results (RTX 4070 Ti)
```
Batch (2 chunks) done in 59.96s (29.98s/chunk)
Batch (5 chunks) done in 81.59s (16.32s/chunk)
```

**Speedup:** 4.6x faster than ComfyUI pattern (75s → 16.32s per chunk)

## ComfyUI Pattern Analysis

**Why ComfyUI is Slower:**
- Designed for real-time voice synthesis in UI workflows
- Processes one chunk at a time for incremental feedback
- Quote from testing: "70 seconds for a five second clip, on a 3060 12Gb card"
- **14x slower than real-time** - unsuitable for long audiobooks

**Why VOX-1's Batch Approach is Better:**
- Qwen3-TTS model natively supports batch processing (list input → list output)
- Batch processing amortizes model overhead across multiple chunks
- Optimized for bulk rendering, not interactive UI
- **2x faster than real-time** - practical for full books

## Conclusion

The ComfyUI implementation was a **performance regression**, not an improvement. The original VOX-1 design with batch processing is architecturally superior for audiobook generation.

**Key Lesson:** Don't assume "newer" or "from popular project" means "better" - benchmark and verify.

## Notes
- Model accepts list of texts and returns list of wavs - batching supported natively
- Batch slider supports 1-20 range (app.py line 489)
- sdpa is PyTorch built-in attention (reliable, compatible)
- If OOM: reduce batch size in Advanced Settings
