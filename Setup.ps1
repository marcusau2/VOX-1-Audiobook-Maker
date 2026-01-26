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
# Use Nuget package - acts as a full portable ZIP (unlike the minimal embeddable zip)
$PythonNugetUrl = "https://www.nuget.org/api/v2/package/python/3.10.11"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"
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

# 1. Install Python (Nuget Portable Method)
if (-not (Test-Path "$PythonSystemDir\python.exe")) {
    Write-Host "[1/4] Downloading Python 3.10 (Portable)..." -ForegroundColor Yellow
    $NugetPath = Join-Path $RootDir "python.zip" # Save as zip to make extraction easier
    Download-File -Url $PythonNugetUrl -OutputPath $NugetPath

    Write-Host "[2/4] Setting up Python..." -ForegroundColor Yellow
    $TempExtract = Join-Path $RootDir "python_temp"
    New-Item -ItemType Directory -Force -Path $TempExtract | Out-Null
    
    Extract-Zip -ZipPath $NugetPath -DestPath $TempExtract
    
    # Move the 'tools' folder content to system_python
    # Nuget package structure: /tools contains the python env
    if (Test-Path "$TempExtract\tools\python.exe") {
        Move-Item -Path "$TempExtract\tools\*" -Destination $PythonSystemDir -Force
    } else {
        # Fallback: maybe structure is flat?
        Move-Item -Path "$TempExtract\*" -Destination $PythonSystemDir -Force
    }
    
    # Cleanup
    Remove-Item $NugetPath -Force
    Remove-Item $TempExtract -Recurse -Force

    if (-not (Test-Path "$PythonSystemDir\python.exe")) {
        Write-Error "Failed to set up Python. python.exe not found."
    }

    Write-Host "Python environment ready." -ForegroundColor Green

    # Install Pip (Nuget package might not have it or it might be old)
    Write-Host "Ensuring Pip is installed..." -ForegroundColor Cyan
    $GetPipPath = Join-Path $RootDir "get-pip.py"
    Download-File -Url $GetPipUrl -OutputPath $GetPipPath
    
    $PipArgs = @(
        "$GetPipPath",
        "--no-warn-script-location",
        "--isolated",
        "--trusted-host", "pypi.org",
        "--trusted-host", "pypi.python.org",
        "--trusted-host", "files.pythonhosted.org"
    )
    
    $Process = Start-Process -FilePath "$PythonSystemDir\python.exe" -ArgumentList $PipArgs -Wait -PassThru
    if ($Process.ExitCode -ne 0) {
        Write-Warning "Pip install reported an issue, but we'll try to proceed."
    }
    Remove-Item $GetPipPath -Force

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