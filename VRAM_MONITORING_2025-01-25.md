# VRAM Monitoring & Batch Size Optimization - 2025-01-25

## Changes Made

### 1. VRAM Logging in Activity Log

**Added real-time VRAM display after each batch:**
```
[18:27:40] Batch 1 (3 chunks) done in 45.32s (15.11s/chunk) | VRAM: 7.2/12.0GB (60%)
```

**Benefits:**
- Detect memory leaks or accumulation
- See when approaching OOM before crash
- Diagnose if processing stalled vs hung

**Modified files:**
- `backend.py` lines 773-782: render_book() batch logging
- `backend.py` lines 1747-1756: _render_from_manifest_data() batch logging

---

### 2. GPU-Specific Batch Size Recommendations

**Added automatic recommendations on startup:**
```
GPU: NVIDIA GeForce RTX 4070 Ti
Total VRAM: 12.0 GB
Available VRAM: 7.1 GB
Current batch size (3) is optimal for your GPU
```

Or if suboptimal:
```
NOTE: For 24GB VRAM, recommended batch size is 10 (current: 3)
      Adjust in Advanced Settings if needed
```

**Recommendation table:**
| GPU VRAM | Recommended Batch | GPUs |
|----------|-------------------|------|
| 24GB+ | 10 | RTX 4090, A5000 |
| 16GB+ | 5 | RTX 4080, 3090 Ti |
| 12GB+ | 3 | RTX 4070 Ti, 3060 12GB |
| 8GB+ | 2 | RTX 4060 Ti, 3060 8GB |
| <8GB | 1 | GTX 1060, etc. |

**New function:**
- `backend.py` lines 329-366: `_suggest_batch_size()`

---

### 3. Default Batch Size Changed

**Changed from 5 → 3:**
- More conservative for common 12GB GPUs
- Accounts for display apps using VRAM
- Users with larger GPUs get recommendation to increase

**Modified:**
- `app.py` line 488: GUI default fallback
- `backend.py` line 267: AudioEngine __init__ default
- `user_settings.json` line 4: User config

---

## How It Works

### Startup Flow
1. App loads, detects GPU (e.g., 4070 Ti 12GB)
2. Suggests batch size: "Recommended batch size is 3"
3. User can adjust in Advanced Settings if needed

### During Rendering
```
[18:27:40] Batch 1 (3 chunks) done in 45.32s (15.11s/chunk) | VRAM: 7.2/12.0GB (60%)
[18:28:25] Batch 2 (3 chunks) done in 44.18s (14.73s/chunk) | VRAM: 7.3/12.0GB (61%)
[18:29:09] Batch 3 (3 chunks) done in 43.95s (14.65s/chunk) | VRAM: 7.3/12.0GB (61%)
```

**What to look for:**
- ✅ **Stable VRAM (±0.5GB):** Normal, healthy
- ⚠️ **Growing VRAM (+1GB/batch):** Memory leak, may OOM soon
- ⚠️ **>95% VRAM:** Too aggressive, reduce batch size
- ⚠️ **No new logs for 2+ min:** Likely stalled/hung

---

## Detecting Stalls

### Symptoms
- Last log shows high VRAM (>90%)
- No new logs for 2+ minutes
- GPU at 100% but no progress

### Diagnosis
**Before this update:**
- No visibility into VRAM state
- Unclear if OOM or just slow

**After this update:**
```
[18:29:09] Batch 3 done | VRAM: 11.8/12.0GB (98%)
[No more logs...]
```
→ Clear indication: approaching OOM, need to reduce batch size

---

## User Actions Based on Logs

### If VRAM is stable at 50-70%
✅ **Good!** Can potentially increase batch size for speed

### If VRAM is 80-90%
⚠️ **Caution:** Close background apps or reduce batch size

### If VRAM is >95%
❌ **Danger:** Reduce batch size immediately
1. Stop render
2. Advanced Settings → Batch Size → Reduce by 1-2
3. Restart render

### If VRAM grows each batch
❌ **Memory leak:** Restart app
1. Stop render
2. Close and reopen app
3. Resume from cached chunks

---

## Testing Different Batch Sizes

**Your GPUs:**
- **4070 Ti (12GB):** Start with 3, test up to 5 if VRAM stable <80%
- **4090 (24GB):** Start with 10, test up to 15 if VRAM stable <80%

**Experiment:**
1. Set batch size in Advanced Settings
2. Render test chapter (50-100 chunks)
3. Watch VRAM in logs
4. If stable <80%, try +1 batch
5. If >90%, try -1 batch

**Goal:** Maximum batch size while keeping VRAM <80% for stability

---

## Implementation Notes

### Why Conservative Defaults?
- Users run display on same GPU (Windows, browsers, apps)
- Display apps can use 1-2GB VRAM
- Better to be safe (batch=3) than OOM (batch=5)
- Power users get recommendation to increase

### Why VRAM After Each Batch?
- Batches complete every 30-90 seconds
- Frequent enough to catch issues early
- Not too spammy (vs per-chunk logging)
- Helps diagnose "is it working or hung?"

### Future Enhancement Ideas
- [ ] Auto-tune batch size during render (start high, reduce if approaching OOM)
- [ ] Pause render if VRAM >95%, prompt user to reduce batch
- [ ] Track VRAM trend (growing/stable/shrinking) and warn
- [ ] Export VRAM graph after render for analysis

---

## Summary

**Problem:** Hard to diagnose OOM or stalls, unclear if batch size is optimal

**Solution:**
1. Show VRAM after every batch (real-time visibility)
2. Recommend batch size on startup (per-GPU optimization)
3. Conservative default (batch=3 for 12GB GPUs)

**Result:** Users can monitor health, tune for their GPU, detect issues early
