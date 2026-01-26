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
$PythonEmbedUrl = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip"
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

# 1. Install Python (Embeddable Method)
if (-not (Test-Path "$PythonSystemDir\python.exe")) {
    Write-Host "[1/5] Downloading Python 3.10 (Embeddable)..." -ForegroundColor Yellow
    $ZipPath = Join-Path $RootDir "python.zip"
    Download-File -Url $PythonEmbedUrl -OutputPath $ZipPath

    Write-Host "[2/5] Extracting Python..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Force -Path $PythonSystemDir | Out-Null
    Extract-Zip -ZipPath $ZipPath -DestPath $PythonSystemDir
    Remove-Item $ZipPath -Force

    # CRITICAL: Enable 'site' package to allow pip/venv to work
    Write-Host "Configuring Python for pip/venv support..." -ForegroundColor Cyan
    $PthFile = Join-Path $PythonSystemDir "python310._pth"
    if (Test-Path $PthFile) {
        $Content = Get-Content $PthFile
        $Content = $Content -replace "#import site", "import site"
        Set-Content -Path $PthFile -Value $Content
    }

    # Install pip manually (Embeddable doesn't have it)
    Write-Host "Installing pip..." -ForegroundColor Cyan
    $GetPipPath = Join-Path $RootDir "get-pip.py"
    Download-File -Url $GetPipUrl -OutputPath $GetPipPath
    
    # Use isolated mode and trusted hosts to avoid network/config issues
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
        Write-Error "Failed to install pip. Exit code: $($Process.ExitCode)"
    }
    Remove-Item $GetPipPath -Force

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