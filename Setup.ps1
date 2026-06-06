# ============================================================================
# VOX-1 Audiobook Maker - Setup Script
# ============================================================================
# Installs Python dependencies for OmniVoice-based VOX-1.
# Requires Python 3.12 and an NVIDIA GPU with CUDA 12.8 compatible drivers.
# ============================================================================

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$RootDir = $PSScriptRoot

Clear-Host
Write-Host "============================================" -ForegroundColor Green
Write-Host "    VOX-1 SETUP" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""

# 1. FIND PYTHON 3.12
$PythonExe = $null
$PythonCandidates = @(
    "$RootDir\system_python\python.exe",
    "$env:USERPROFILE\scoop\apps\python312\current\python.exe",
    "python"
)

foreach ($candidate in $PythonCandidates) {
    try {
        $version = & $candidate --version 2>&1
        if ($version -match "Python 3\.12") {
            $PythonExe = $candidate
            Write-Host "[OK] Found Python 3.12: $PythonExe" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

if (-not $PythonExe) {
    Write-Host "[X] Python 3.12 not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install Python 3.12 via one of these methods:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Option 1 (Scoop, recommended):"
    Write-Host "    scoop install python@3.12"
    Write-Host ""
    Write-Host "  Option 2 (Official installer):"
    Write-Host "    https://www.python.org/downloads/release/python-31210/"
    Write-Host ""
    Write-Host "Then run this script again."
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# 2. UPGRADE PIP
Write-Host ""
Write-Host "[1/3] Upgrading pip..." -ForegroundColor Yellow
& $PythonExe -m pip install --upgrade pip --no-warn-script-location
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] pip upgrade had warnings (non-fatal)" -ForegroundColor Yellow
}

# 3. INSTALL DEPENDENCIES
Write-Host ""
Write-Host "[2/3] Installing Python dependencies..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Cyan
Write-Host ""

& $PythonExe -m pip install -r "$RootDir\requirements.txt"

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[X] Some packages failed to install." -ForegroundColor Red
    Write-Host "    Check the error messages above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  - Ensure CUDA 12.8 drivers are installed"
    Write-Host "  - Run: pip install torch==2.8.0+cu128 --extra-index-url https://download.pytorch.org/whl/cu128"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# 4. CHECK FFMPEG
Write-Host ""
Write-Host "[3/3] Checking FFmpeg..." -ForegroundColor Yellow
$ffmpegFound = $false

try {
    $result = & ffmpeg -version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] FFmpeg found in PATH" -ForegroundColor Green
        $ffmpegFound = $true
    }
} catch {}

if (-not $ffmpegFound) {
    $BundledFFmpeg = "$RootDir\ffmpeg_bundle\ffmpeg.exe"
    if (Test-Path $BundledFFmpeg) {
        Write-Host "[OK] FFmpeg found in bundle: ffmpeg_bundle\ffmpeg.exe" -ForegroundColor Green
        $ffmpegFound = $true
    }
}

if (-not $ffmpegFound) {
    Write-Host "[!] FFmpeg not found. M4B chapter support requires FFmpeg." -ForegroundColor Yellow
    Write-Host "    Download from: https://ffmpeg.org/download.html" -ForegroundColor Yellow
    Write-Host "    Or place ffmpeg.exe in: ffmpeg_bundle/" -ForegroundColor Yellow
}

# 5. VERIFY OMNIVOICE
Write-Host ""
Write-Host "Verifying OmniVoice installation..." -ForegroundColor Yellow
try {
    $output = & $PythonExe -c "import omnivoice; print(omnivoice.__version__)" 2>&1
    Write-Host "[OK] OmniVoice $output installed" -ForegroundColor Green
} catch {
    Write-Host "[!] OmniVoice import failed. Trying reinstall..." -ForegroundColor Yellow
    & $PythonExe -m pip install omnivoice
}

# 6. DONE
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "    SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Launch with: RUN-VOX-1.bat" -ForegroundColor Cyan
Write-Host ""
Write-Host "On first launch, the OmniVoice model (~3.5 GB)" -ForegroundColor Cyan
Write-Host "will download automatically to the models/ folder." -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"
