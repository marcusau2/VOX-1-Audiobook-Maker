# Flash Attention 2 - Performance Optimization

## What is Flash Attention 2?

Flash Attention 2 is an optimized CUDA kernel implementation for transformer attention operations that provides:

- **2-4x less VRAM usage** during audio generation
- **2x faster inference** speed
- **Higher batch sizes** without running out of memory

## Performance Comparison

### Without Flash Attention (Standard)
- **12GB GPU (RTX 4070 Ti):** Batch 2-3 stable
- **24GB GPU (RTX 4090):** Batch 5-7 stable

### With Flash Attention 2
- **12GB GPU (RTX 4070 Ti):** Batch 5-20 possible
- **24GB GPU (RTX 4090):** Batch 20-64 possible

**Speed improvement:** Batch 20 can be 10x faster than Batch 2!

## Requirements

- **Operating System:** Windows 10/11 (64-bit)
- **GPU:** NVIDIA RTX 3000/4000 series (Ampere or Ada Lovelace architecture)
- **CUDA:** 12.8 (already included with PyTorch installation)
- **Python:** 3.10 (already installed with VOX-1)

**Supported GPUs:**
- RTX 3060, 3060 Ti, 3070, 3070 Ti, 3080, 3080 Ti, 3090, 3090 Ti
- RTX 4060, 4060 Ti, 4070, 4070 Ti, 4080, 4090

## Installation

### Automatic Installation (Recommended)

1. **Run the installer:**
   ```
   Double-click: Install-Flash-Attention.bat
   ```

2. **Wait for installation** (takes 1-2 minutes)

3. **Verify installation** - The script will confirm if successful

### Manual Installation

If the automatic installer doesn't work:

```powershell
# From the VOX-1-Audiobook-Maker directory
system_python\python.exe -m pip install https://github.com/mjun0812/flash-attention-prebuild-wheels/releases/download/v0.4.10/flash_attn-2.7.4+cu128torch2.7-cp310-cp310-win_amd64.whl
```

### Verify Installation

```powershell
system_python\python.exe -c "import flash_attn; print(flash_attn.__version__)"
```

Expected output: `2.7.4`

## Usage

### 1. Enable Flash Attention in VOX-1

1. Launch VOX-1: `RUN-VOX-1.bat`
2. Go to **Advanced Settings** tab
3. Find **"Attention Implementation"** dropdown
4. Select **"auto"** (tries Flash Attention, falls back gracefully) or **"flash_attention_2"** (forces it)
5. Click **"Apply Settings"**
6. Wait for engine to reload

### 2. Verify It's Working

Check the **Activity Log** when model loads. You should see:
```
Flash Attention 2.7.4 detected - attempting to use it
✅ Flash Attention 2 enabled successfully
```

### 3. Test Higher Batch Sizes

1. In **Advanced Settings**, increase **Batch Size**
2. Start with conservative values:
   - **12GB GPU:** Try batch 5, then 7, then 10
   - **24GB GPU:** Try batch 10, then 15, then 20
3. Monitor VRAM usage in Activity Log
4. If generation completes successfully, try increasing further

## Attention Implementation Options

The **Advanced Settings** dropdown provides several options:

| Option | Description | When to Use |
|--------|-------------|-------------|
| **auto** | Tries Flash Attention if available, falls back to SDPA or eager | **Recommended** - Best compatibility |
| **flash_attention_2** | Forces Flash Attention 2 (errors if not available) | When you want to ensure Flash Attention is used |
| **sdpa** | PyTorch's built-in Scaled Dot Product Attention | If Flash Attention has issues |
| **eager** | Standard attention (no optimization) | Baseline / troubleshooting |

## Troubleshooting

### Installation Fails

**Error:** `Failed to download Flash Attention wheel`
- Check your internet connection
- The GitHub release may be temporarily unavailable
- Try manual installation with the command above

**Error:** `Installation verification failed`
- Your GPU may not support Flash Attention
- VOX-1 will still work with standard attention
- Try using "sdpa" instead in the dropdown

### Flash Attention Not Working

**Check Activity Log:**
- If you see "Flash Attention not installed", rerun the installer
- If you see "using default attention", Flash Attention isn't available

**Try different attention methods:**
1. Set to "sdpa" (PyTorch's built-in optimization)
2. Set to "eager" (standard attention, slowest)

### Out of Memory Errors

Even with Flash Attention, very high batch sizes can exceed VRAM:
- **Reduce batch size** by 2-3
- **Check other applications** using GPU
- **Restart VOX-1** to clear VRAM

## Uninstallation

To remove Flash Attention:

```powershell
system_python\python.exe -m pip uninstall flash-attn -y
```

VOX-1 will automatically fall back to standard attention methods.

## Technical Details

### How Flash Attention Works

Flash Attention 2 optimizes the attention mechanism in transformer models by:
1. **Fused operations** - Combines multiple GPU operations into one kernel
2. **Tiling** - Processes attention in smaller blocks that fit in GPU cache
3. **Recomputation** - Recomputes some values instead of storing them

This reduces memory from O(N²) to O(N) for sequence length N.

### References

- **Paper:** [FlashAttention-2: Faster Attention with Better Parallelism](https://arxiv.org/abs/2307.08691)
- **Prebuilt Wheels:** [mjun0812/flash-attention-prebuild-wheels](https://github.com/mjun0812/flash-attention-prebuild-wheels)
- **Original Repo:** [Dao-AILab/flash-attention](https://github.com/Dao-AILab/flash-attention)

## FAQ

**Q: Is Flash Attention required?**
A: No, VOX-1 works fine without it. Flash Attention is an optional performance optimization.

**Q: Will it work on AMD GPUs?**
A: No, Flash Attention 2 requires NVIDIA GPUs. AMD users can use "sdpa" mode.

**Q: Does it reduce audio quality?**
A: No, Flash Attention produces identical outputs. It only optimizes how attention is computed.

**Q: Can I use it on older GPUs (GTX 1000/2000 series)?**
A: No, Flash Attention requires RTX 3000+ (Ampere architecture or newer).

**Q: What about Linux/Mac?**
A: This installer is Windows-only. Linux users can build from source. Mac is not supported.

## Support

If you encounter issues:
1. Check the Activity Log for error messages
2. Try different attention implementations in the dropdown
3. Report issues on GitHub with your:
   - GPU model
   - CUDA version
   - Error messages from Activity Log
