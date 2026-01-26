# ============================================================================
# VOX-1 Audiobook Maker - Setup Script
# ============================================================================
# This script handles the downloading and installation of all dependencies.
# It uses the "Embeddable Zip" method for a truly portable Python installation.
# ============================================================================

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Configuration
$PythonVersion = "3.10.11"
$PythonInstallerUrl = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
$FFmpegUrl = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"

$RootDir = $PSScriptRoot
$PythonSystemDir = Join-Path $RootDir "system_python"
$VenvDir = Join-Path $RootDir "venv"
$FFmpegDir = Join-Path $RootDir "ffmpeg_bundle"

# Helper Function: Download File with Progress
function Download-File {
    param([string]$Url, [string]$OutputPath)
    Write-Host "Downloading: $(Split-Path $OutputPath -Leaf)..." -ForegroundColor Cyan
    try {
        Invoke-WebRequest -Uri $Url -OutFile $OutputPath -UseBasicParsing
    } catch {
        Write-Error "Failed to download $Url. Error: $_"
    }
}

# Helper Function: Extract Zip
function Extract-Zip {
    param([string]$ZipPath, [string]$DestPath)
    Write-Host "Extracting $(Split-Path $ZipPath -Leaf)..." -ForegroundColor Cyan
    Expand-Archive -Path $ZipPath -DestinationPath $DestPath -Force
}

Clear-Host
Write-Host "============================================" -ForegroundColor Green
Write-Host "    VOX-1 SETUP - AUTO INSTALLER" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "This script will install a private Python environment"
Write-Host "and all dependencies for VOX-1."
Write-Host ""

# 1. Install Python (Private Full Install)
if (-not (Test-Path "$PythonSystemDir\python.exe")) {
    Write-Host "[1/4] Downloading Python 3.10 (Full Installer)..." -ForegroundColor Yellow
    $InstallerPath = Join-Path $RootDir "python_installer.exe"
    Download-File -Url $PythonInstallerUrl -OutputPath $InstallerPath

    Write-Host "[2/4] Installing Python (Local)..." -ForegroundColor Yellow
    
    # Arguments for a private, passive install
    # /passive = show progress bar but don't wait for input
    # InstallAllUsers=0 = install to target directory only
    # PrependPath=0 = don't modify system PATH
    # Include_test=0 = skip test suite
    $InstallArgs = @(
        "/passive",
        "InstallAllUsers=0",
        "PrependPath=0",
        "Include_test=0",
        "Include_pip=1",
        "Include_tcltk=1",
        "TargetDir=$PythonSystemDir"
    )
    
    Write-Host "Running installer..." -ForegroundColor DarkGray
    $Process = Start-Process -FilePath $InstallerPath -ArgumentList $InstallArgs -Wait -PassThru
    
    if ($Process.ExitCode -ne 0) {
        Write-Error "Python installation failed with exit code $($Process.ExitCode)."
    }
    
    Remove-Item $InstallerPath -Force
    Write-Host "Python installed successfully." -ForegroundColor Green
} else {
    Write-Host "Python already installed." -ForegroundColor Green
}

# 2. Install FFmpeg
if (-not (Test-Path "$FFmpegDir\ffmpeg.exe")) {
    Write-Host "[3/4] Setting up FFmpeg..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $FFmpegDir | Out-Null
    $FFmpegZip = Join-Path $RootDir "ffmpeg.zip"
    $TempDir = Join-Path $RootDir "ffmpeg_temp"
    
    Download-File -Url $FFmpegUrl -OutputPath $FFmpegZip
    Extract-Zip -ZipPath $FFmpegZip -DestPath $TempDir
    
    # Move binaries
    $ExtractedRoot = Get-ChildItem -Path $TempDir -Directory | Select-Object -First 1
    Copy-Item "$($ExtractedRoot.FullName)\bin\ffmpeg.exe" "$FFmpegDir\ffmpeg.exe" -Force
    Copy-Item "$($ExtractedRoot.FullName)\bin\ffprobe.exe" "$FFmpegDir\ffprobe.exe" -Force
    
    # Cleanup
    Remove-Item $FFmpegZip -Force
    Remove-Item $TempDir -Recurse -Force
    Write-Host "FFmpeg installed." -ForegroundColor Green
} else {
    Write-Host "FFmpeg already installed." -ForegroundColor Green
}

# 3. Install Dependencies
Write-Host "[4/4] Installing Python Dependencies..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes (downloading PyTorch ~2.5GB)..." -ForegroundColor Cyan

# Use the embedded python's pip directly
$PythonExe = "$PythonSystemDir\python.exe"
& $PythonExe -m pip install --upgrade pip
& $PythonExe -m pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "WARNING: Some packages failed to install." -ForegroundColor Red
    Write-Host "You can try running this installer again." -ForegroundColor Red
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "    INSTALLATION COMPLETE!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host "You can now launch the app using RUN-VOX-1.bat"
Write-Host ""
Read-Host "Press Enter to exit..."