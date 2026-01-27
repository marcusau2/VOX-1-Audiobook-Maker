# ============================================================================
# VOX-1 Audiobook Maker - Flash Attention 2 Installation Script
# ============================================================================
# This script installs Flash Attention 2 for improved performance:
# - 2-4x less VRAM usage during generation
# - 2x faster inference
# - Enables higher batch sizes (5-20 on 12GB, 20-64 on 24GB)
# ============================================================================

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Configuration
$FlashAttnVersion = "2.7.4"
$ReleaseVersion = "v0.4.10"
$CudaVersion = "cu128"  # CUDA 12.8
$TorchVersion = "torch2.7"
$PythonVersion = "cp310"  # Python 3.10
$Platform = "win_amd64"

# Construct wheel URL
$WheelFilename = "flash_attn-${FlashAttnVersion}+${CudaVersion}${TorchVersion}-${PythonVersion}-${PythonVersion}-${Platform}.whl"
$WheelUrl = "https://github.com/mjun0812/flash-attention-prebuild-wheels/releases/download/${ReleaseVersion}/${WheelFilename}"

$RootDir = $PSScriptRoot
$PythonSystemDir = Join-Path $RootDir "system_python"
$PythonExe = Join-Path $PythonSystemDir "python.exe"

# Helper Function: Download File
function Download-File {
    param([string]$Url, [string]$OutputPath)
    Write-Host "Downloading: $(Split-Path $OutputPath -Leaf)..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri $Url -OutFile $OutputPath -UseBasicParsing
    } catch {
        Write-Error "Failed to download $Url. Error: $_"
    }
}

Clear-Host
Write-Host "============================================" -ForegroundColor Green
Write-Host "    FLASH ATTENTION 2 INSTALLER" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "What is Flash Attention 2?" -ForegroundColor Cyan
Write-Host "- Optimized CUDA kernels for transformer attention"
Write-Host "- 2-4x less VRAM usage during generation"
Write-Host "- 2x faster inference speed"
Write-Host "- Enables much higher batch sizes:"
Write-Host "  * 12GB GPU: Batch 5-20 (vs 2-3 without)"
Write-Host "  * 24GB GPU: Batch 20-64 (vs 5-7 without)"
Write-Host ""
Write-Host "Requirements:" -ForegroundColor Cyan
Write-Host "- Windows 10/11"
Write-Host "- NVIDIA RTX 3000/4000 series GPU"
Write-Host "- CUDA 12.8 (already installed with PyTorch)"
Write-Host "- Python 3.10 (your current version)"
Write-Host ""

# 1. CHECK PREREQUISITES
Write-Host "[1/4] Checking prerequisites..." -ForegroundColor Yellow

# Check if Python exists
if (-not (Test-Path $PythonExe)) {
    Write-Host ""
    Write-Host "ERROR: Python not found at $PythonExe" -ForegroundColor Red
    Write-Host "Please run Install-VOX-1.bat first to set up Python." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit..."
    exit 1
}

# Check Python version
$PythonVersionOutput = & $PythonExe --version 2>&1
Write-Host "Found: $PythonVersionOutput" -ForegroundColor Green

# Check CUDA availability
Write-Host "Checking CUDA availability..." -ForegroundColor Cyan
$CudaCheck = & $PythonExe -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}'); print(f'CUDA Version: {torch.version.cuda}')" 2>&1
Write-Host $CudaCheck

if ($CudaCheck -notmatch "CUDA Available: True") {
    Write-Host ""
    Write-Host "WARNING: CUDA not available!" -ForegroundColor Yellow
    Write-Host "Flash Attention requires CUDA-capable GPU." -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 0
    }
}

# Check GPU model
Write-Host "Detecting GPU..." -ForegroundColor Cyan
$GpuCheck = & $PythonExe -c "import torch; print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}'); print(f'Compute Capability: {torch.cuda.get_device_capability(0) if torch.cuda.is_available() else \"N/A\"}')" 2>&1
Write-Host $GpuCheck

# Check if already installed
Write-Host "Checking if Flash Attention is already installed..." -ForegroundColor Cyan
$FlashAttnCheck = & $PythonExe -c "import flash_attn; print(f'Flash Attention {flash_attn.__version__} is already installed')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host $FlashAttnCheck -ForegroundColor Green
    Write-Host ""
    $reinstall = Read-Host "Reinstall Flash Attention? (y/n)"
    if ($reinstall -ne "y") {
        Write-Host "Installation cancelled." -ForegroundColor Yellow
        Read-Host "Press Enter to exit..."
        exit 0
    }
}

Write-Host ""
Write-Host "[2/4] Downloading Flash Attention 2..." -ForegroundColor Yellow
Write-Host "Version: $FlashAttnVersion" -ForegroundColor Cyan
Write-Host "CUDA: $CudaVersion (12.8)" -ForegroundColor Cyan
Write-Host "URL: $WheelUrl" -ForegroundColor Cyan
Write-Host ""

$WheelPath = Join-Path $RootDir $WheelFilename

# Download the wheel
Download-File -Url $WheelUrl -OutputPath $WheelPath

if (-not (Test-Path $WheelPath)) {
    Write-Host ""
    Write-Host "ERROR: Failed to download Flash Attention wheel." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host ""
Write-Host "[3/4] Installing Flash Attention 2..." -ForegroundColor Yellow
Write-Host "This may take a minute..." -ForegroundColor Cyan
Write-Host ""

# Install the wheel
& $PythonExe -m pip install $WheelPath --force-reinstall --no-deps

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Installation failed." -ForegroundColor Red
    Write-Host "The wheel may not be compatible with your system." -ForegroundColor Red
    Write-Host ""
    Read-Host "Press Enter to exit..."

    # Cleanup
    if (Test-Path $WheelPath) {
        Remove-Item $WheelPath -Force
    }
    exit 1
}

# Cleanup wheel file
Remove-Item $WheelPath -Force

Write-Host ""
Write-Host "[4/4] Verifying installation..." -ForegroundColor Yellow

# Verify installation
$VerifyResult = & $PythonExe -c "import flash_attn; print(f'Flash Attention {flash_attn.__version__} installed successfully')" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "    INSTALLATION COMPLETE!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host $VerifyResult -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Launch VOX-1 using RUN-VOX-1.bat"
    Write-Host "2. Go to Advanced Settings tab"
    Write-Host "3. Set 'Attention Implementation' to 'auto' or 'flash_attention_2'"
    Write-Host "4. Click 'Apply Settings'"
    Write-Host "5. Check Activity Log - should show 'Flash Attention 2.7.4 detected'"
    Write-Host "6. Try higher batch sizes:"
    Write-Host "   - 12GB GPU: Try batch 5-10"
    Write-Host "   - 24GB GPU: Try batch 10-20"
    Write-Host ""
    Write-Host "Performance Expectations:" -ForegroundColor Cyan
    Write-Host "- 2-4x less VRAM usage"
    Write-Host "- 2x faster generation"
    Write-Host "- Higher batch sizes possible"
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "ERROR: Installation verification failed." -ForegroundColor Red
    Write-Host $VerifyResult -ForegroundColor Red
    Write-Host ""
    Write-Host "Flash Attention may not be compatible with your GPU." -ForegroundColor Yellow
    Write-Host "VOX-1 will still work without it using standard attention." -ForegroundColor Yellow
    Write-Host ""
}

Read-Host "Press Enter to exit..."
