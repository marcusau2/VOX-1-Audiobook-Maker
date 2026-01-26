# ============================================================================
# VOX-1 Audiobook Maker - Setup Script (Standalone Version)
# ============================================================================
# This script uses a "Standalone" Python build.
# - It is fully portable (no registry, no installer).
# - It includes Tkinter/GUI support (unlike the standard Embeddable zip).
# ============================================================================

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Configuration
# Using indygreg's python-build-standalone. It creates a full, portable environment with Tkinter.
$PythonDownloadUrl = "https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-x86_64-pc-windows-msvc-shared-install_only.tar.gz"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$FFmpegUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"      

$RootDir = $PSScriptRoot
$PythonSystemDir = Join-Path $RootDir "system_python"
$FFmpegDir = Join-Path $RootDir "ffmpeg_bundle"

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
Write-Host "    VOX-1 SETUP - PORTABLE REPAIR" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "Installing Standalone Python (Portable + Tkinter included)."
Write-Host ""

# 1. CLEANUP: Remove old broken python
if (Test-Path $PythonSystemDir) {
    Write-Host "Cleaning up old Python environment..." -ForegroundColor Yellow
    Remove-Item -Path $PythonSystemDir -Recurse -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# 2. INSTALL PYTHON (Standalone Build)
if (-not (Test-Path "$PythonSystemDir\python.exe")) {
    Write-Host "[1/4] Downloading Python 3.10 (Standalone)..." -ForegroundColor Yellow
    $ArchiveName = "python_standalone.tar.gz"
    $ArchivePath = Join-Path $RootDir $ArchiveName

    Download-File -Url $PythonDownloadUrl -OutputPath $ArchivePath

    Write-Host "[2/4] Extracting Python..." -ForegroundColor Yellow
    # Windows 10/11 includes 'tar.exe' natively. We use it to handle .tar.gz
    # We extract to a temp folder first to handle the internal folder structure
    $TempExtract = Join-Path $RootDir "python_temp"
    New-Item -ItemType Directory -Force -Path $TempExtract | Out-Null

    try {
        tar -xf $ArchivePath -C $TempExtract
    } catch {
        Write-Error "Failed to extract tar.gz. Ensure you are on Windows 10 or 11."
    }

    # The archive usually has a subfolder named 'python'. Move its contents.
    $InnerPython = Join-Path $TempExtract "python"
    if (Test-Path $InnerPython) {
        Move-Item -Path "$InnerPython" -Destination $PythonSystemDir -Force
    } else {
        # Fallback if structure is different
        Move-Item -Path "$TempExtract\*" -Destination $PythonSystemDir -Force
    }

    # Cleanup
    Remove-Item $ArchivePath -Force
    Remove-Item $TempExtract -Recurse -Force

    if (-not (Test-Path "$PythonSystemDir\python.exe")) {
        Write-Error "Failed to setup Python. python.exe not found after extraction."
    }

    Write-Host "Python environment ready." -ForegroundColor Green

} else {
    Write-Host "Python already installed." -ForegroundColor Green
}

# 3. INSTALL FFMPEG
if (-not (Test-Path "$FFmpegDir\ffmpeg.exe")) {
    Write-Host "[3/4] Setting up FFmpeg..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $FFmpegDir | Out-Null
    $FFmpegZip = Join-Path $RootDir "ffmpeg.zip"
    $TempDir = Join-Path $RootDir "ffmpeg_temp"

    Download-File -Url $FFmpegUrl -OutputPath $FFmpegZip
    Expand-Archive -Path $FFmpegZip -DestinationPath $TempDir -Force

    $ExtractedRoot = Get-ChildItem -Path $TempDir -Directory | Select-Object -First 1
    Copy-Item "$($ExtractedRoot.FullName)\bin\ffmpeg.exe" "$FFmpegDir\ffmpeg.exe" -Force
    Copy-Item "$($ExtractedRoot.FullName)\bin\ffprobe.exe" "$FFmpegDir\ffprobe.exe" -Force

    Remove-Item $FFmpegZip -Force
    Remove-Item $TempDir -Recurse -Force
    Write-Host "FFmpeg installed." -ForegroundColor Green
} else {
    Write-Host "FFmpeg already installed." -ForegroundColor Green
}

# 4. INSTALL DEPENDENCIES
Write-Host "[4/4] Installing Python Dependencies..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Cyan

$PythonExe = "$PythonSystemDir\python.exe"

# 4a. Upgrade build tools
# Note: Standalone builds usually come with pip, but we upgrade to be safe
& $PythonExe -m pip install --upgrade pip setuptools wheel --no-warn-script-location

# 4b. Install requirements with NO BUILD ISOLATION
# This prevents the 'BackendUnavailable' error
& $PythonExe -m pip install -r requirements.txt --no-build-isolation

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Some packages failed to install." -ForegroundColor Red
    Write-Host "You can try running this installer again." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "    SETUP COMPLETE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "You can now launch the app using RUN-VOX-1.bat"
Write-Host ""
Read-Host "Press Enter to exit..."
