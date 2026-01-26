# VOX-1 Audiobook Generator - Current Status

**Last Updated:** 2025-01-25
**Version:** Production-ready with optimized batch processing

---

## Current Performance

### Rendering Speed
- **16.32s per chunk** (batch size 5)
- **~2x faster than real-time** for audiobook generation
- **4.6x faster** than ComfyUI sequential implementation

### Benchmark Comparison
| Implementation | Speed | Notes |
|---------------|-------|-------|
| **VOX-1 (Current)** | 16s/chunk | Batch processing, optimal |
| VOX-1 (Pre-ComfyUI) | 50-60s/chunk | No batching |
| ComfyUI Pattern | 75s/chunk | Sequential only, 14x slower than real-time |

---

## Current Configuration

### Settings (user_settings.json)
```json
{
  "batch_size": 5,          // Process 5 chunks at once
  "chunk_size": 500,        // ~500 chars per chunk
  "attention_mode": "sdpa", // PyTorch built-in (reliable)
  "temperature": 0.7,
  "repetition_penalty": 1.05
}
```

### Model Configuration (backend.py)
- **Voice Design/Cloning:** 1.7B model (high quality)
- **Book Rendering:** 0.6B model (fast, efficient)
- **max_new_tokens:** 4096 (optimal for quality)
- **Batching:** Enabled (processes batch_size chunks simultaneously)

---

## Features

### Core Functionality
✅ **Voice Design** - Create voices from text descriptions
✅ **Voice Cloning** - Clone from 10-30s audio samples
✅ **Smart Import** - Auto-optimize voice reference audio
✅ **EPUB/PDF Processing** - Extract structured chapters (BookSmith)
✅ **M4B Output** - Audiobooks with chapter markers
✅ **Batch Processing** - 5 chunks at once (configurable 1-20)
✅ **Resume Support** - Chunk caching for interrupted renders

### Supported Formats
- **Input:** TXT, EPUB, PDF, JSON manifest
- **Output:** MP3 (single file), M4B (with chapters)
- **Voice:** WAV, MP3 (reference audio)

---

## System Requirements

- **OS:** Windows 10/11 64-bit
- **GPU:** NVIDIA GPU with 6GB+ VRAM (12GB recommended)
- **CUDA:** 12.1 or higher
- **Python:** 3.10.8 (for development)

---

## File Structure

```
Audiobook Maker/
├── app.py                    # GUI (CustomTkinter)
├── backend.py                # Audio engine (batch processing)
├── build.py                  # PyInstaller configuration
├── user_settings.json        # User preferences
├── requirements.txt          # Python dependencies
│
├── booksmith_module/         # EPUB/PDF extraction
│   ├── core.py              # Text cleaning
│   └── processors.py        # EPUB/PDF processors
│
├── Output/                   # Generated audiobooks (MP3/M4B)
├── VOX-Output/              # Smart Import optimized audio
├── temp_work/               # Chunk cache (resume support)
├── ffmpeg_bundle/           # Bundled FFmpeg
│
└── dist/Vox-1/              # Built executable
```

---

## Recent Changes (2025-01-25)

### Performance Restoration
**Problem:** Rendering degraded to 75s/chunk after implementing ComfyUI patterns

**Root Cause:** ComfyUI's sequential "one chunk at a time" pattern disabled batching

**Solution:** Restored batch processing
- Model accepts list of texts → returns list of wavs
- Process `batch_size` chunks simultaneously
- Resulted in 4.6x speedup (75s → 16s per chunk)

**Files Modified:**
- `backend.py`: Lines 673-821 (render_book), Lines 1675-1745 (_render_from_manifest_data)
- `user_settings.json`: batch_size=5, attention_mode="sdpa"

---

## Known Issues & Limitations

### Attention Modes
❌ **sage_attn** - Tested slower than sdpa (56-71s vs 50-60s)
❌ **flash_attn** - Not compatible with Qwen3-TTS architecture
✅ **sdpa** - PyTorch built-in, reliable, recommended
✅ **eager** - Standard fallback (slower but always works)

### Model Behavior
- Batch processing is for same-voice sequential chunks (works well)
- Model designed for multi-voice batching also handles sequential chunks efficiently
- Sequential processing (ComfyUI pattern) is significantly slower for audiobooks

---

## Development Notes

### Running from Source
```bash
cd "E:\Gemini Projects\Audiobook Maker"
py -3.10 app.py
```

### Building Executable
```bash
py -3.10 build.py
# Output: dist/Vox-1/Vox-1.exe
```

### Testing Performance
1. Load master voice
2. Load book (EPUB/TXT/JSON)
3. Check Advanced Settings: batch_size=5
4. Start render
5. Monitor log: `Batch (5 chunks) done in XXs (Xs/chunk)`

---

## Documentation

### Active Documents
- `PROJECT_STATUS.md` (this file) - Current state overview
- `PERFORMANCE_REVERT_2025-01-25.md` - Recent optimization details
- `booksmith_module/README.md` - EPUB/PDF processing module

### Archived Documents
- `docs_archive/` - Historical documentation and old session handoffs

---

## Support

### Common Issues

**Slow rendering (>30s/chunk):**
- Check batch_size in Advanced Settings (should be 5)
- Verify attention_mode is "sdpa" or "auto"
- Check max_new_tokens=4096 in backend.py

**Out of memory:**
- Reduce batch_size (try 3 or 2)
- Close other GPU applications
- Use 0.6B model for rendering

**App won't start:**
- Verify Python 3.10.8 installed
- Run: `pip install -r requirements.txt`
- Check CUDA 12.1+ installed

---

## Future Enhancements

**Potential Improvements:**
- [ ] Multi-voice dialogue support (different voices per character)
- [ ] Real-time preview during rendering
- [ ] GPU memory auto-tuning for batch size
- [ ] Additional output formats (OPUS, FLAC)

**Not Recommended:**
- ❌ flash-attn integration (incompatible)
- ❌ sage-attn (tested slower)
- ❌ ComfyUI sequential pattern (4.6x slower)
