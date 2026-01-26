# Documentation Cleanup - 2025-01-25

## Summary

Consolidated 30+ scattered documentation files into 3 core documents for clarity.

---

## New Documentation Structure

### Root Directory (Active Docs)
✅ **README.md** - Quick start, basic usage, troubleshooting
✅ **PROJECT_STATUS.md** - Comprehensive current state, performance, configuration
✅ **PERFORMANCE_REVERT_2025-01-25.md** - Recent optimization details and ComfyUI comparison

### Module Documentation
✅ **booksmith_module/README.md** - EPUB/PDF processing module

### Archive
📦 **docs_archive/** - Outdated documentation (25+ files)
📦 **docs_archive/ARCHIVE_INDEX.md** - Explains what's archived and why

---

## Archived Documents (25 files)

### Failed Optimization Attempts
- `FLASH_ATTN_IMPLEMENTATION.md`
- `FLASH_ATTN_INSTALLATION_GUIDE.md`
- `FLASH_ATTN_ANALYSIS.md`
- `FLASH_ATTN_WORKING.md`
- `CURRENT_STATUS_FLASH_ATTN.md`
- `SAGE_ATTENTION_GUIDE.md`

**Why:** Tested slower than standard sdpa attention

### Performance Investigation
- `COMFYUI_VS_VOX1_COMPARISON.md`
- `PERFORMANCE_FIX_APPLIED.md`
- `REAL_FIX_APPLIED.md`
- `MAX_NEW_TOKENS_FIX.md`

**Why:** Superseded by PERFORMANCE_REVERT_2025-01-25.md

### Old Session Handoffs
- `SESSION_HANDOFF.md`
- `SESSION_HANDOFF_FINAL.md`
- `SESSION_HANDOFF_NEXT.md`

**Why:** Pre-batch processing restoration, outdated

### Historical Notes
- `BUILD_COMPLETE.md`
- `UPGRADE_COMPLETE.md`
- `CRITICAL_BUG_HANDOFF.md`
- `JSON_MANIFEST_FEATURE.md`
- `CHANGES_JSON_SUPPORT.md`
- `IMPLEMENTATION_SUMMARY.md`
- `INTEGRATION_GUIDE.md`
- `INSTRUCTIONS_FOR_CLAUDE.md`
- `BOOKSMITH_INTEGRATION.md`
- `VOX1_COMPLETE_GUIDE.md`
- `VRAM_MANAGEMENT.md`
- `TXT_ONLY_UPDATE.md`
- `SMART_IMPORT_IMPLEMENTATION.md`
- `CHAPTER_M4B_IMPLEMENTATION.md`
- `BUILD_VERIFICATION.md`

**Why:** Features now integrated, superseded by PROJECT_STATUS.md

---

## Key Findings Documented

### Performance Comparison (in PERFORMANCE_REVERT_2025-01-25.md)
| Implementation | Speed per Chunk |
|---------------|-----------------|
| **VOX-1 (Current)** | **16.32s** |
| VOX-1 (Pre-batch) | 50-60s |
| VOX-1 (ComfyUI Pattern) | 75s |
| ComfyUI Benchmark | 14x slower than real-time |

**Conclusion:** ComfyUI sequential pattern was a performance regression, not an improvement.

### Current Configuration (in PROJECT_STATUS.md)
- **batch_size:** 5 (configurable 1-20)
- **max_new_tokens:** 4096
- **attention_mode:** sdpa (PyTorch built-in)
- **Batch processing:** Restored and working

---

## Benefits of Cleanup

✅ **Single source of truth** - PROJECT_STATUS.md
✅ **Clear entry point** - README.md
✅ **No conflicting info** - Old docs archived
✅ **Easier onboarding** - 3 files vs 30+
✅ **Historical reference** - Archive preserved with index

---

## For Future Claude Sessions

**Start here:**
1. Read `README.md` for quick overview
2. Read `PROJECT_STATUS.md` for comprehensive details
3. Read `PERFORMANCE_REVERT_2025-01-25.md` for recent changes

**Don't read:**
- Anything in `docs_archive/` (outdated)
- Unless investigating historical decisions (see ARCHIVE_INDEX.md)

---

## Maintenance

**When adding new features:**
- Update `PROJECT_STATUS.md` (comprehensive)
- Update `README.md` if user-facing changes
- Create dated `FEATURE_NAME_YYYY-MM-DD.md` for complex changes
- Archive after integrating into PROJECT_STATUS.md

**When fixing bugs:**
- Update `PROJECT_STATUS.md` Known Issues section
- Create `BUGFIX_NAME_YYYY-MM-DD.md` if complex
- Archive after confirming fix is stable

---

**Documentation is now clean and maintainable.**
