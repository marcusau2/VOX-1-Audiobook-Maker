@echo off
cd /d "%~dp0"
echo ========================================================
echo    VOX-1 Audiobook Maker - Setup
echo ========================================================
echo.
echo Features:
echo   - FasterQwen3TTS enabled (3-4x real-time speed)
echo   - CUDA graphs supported (requires PyTorch 2.5.1+)
echo   - Optimized for NVIDIA GPUs (RTX 3000/4000 series)
echo.
echo System Requirements:
echo   - NVIDIA GPU with CUDA support (GTX 1000 series or newer)
echo   - 8GB+ VRAM recommended (12GB+ for best performance)
echo   - Windows 10/11 with PowerShell
echo.
echo NOTE: First audio generation will take 10-30 seconds
echo       (CUDA graph capture), then subsequent generations
echo       will be much faster (under 1 second).
echo.
echo ========================================================
echo.

REM Check if PowerShell is available
where powershell >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell is not found on this system.
    echo Please install PowerShell to continue.
    pause
    exit /b 1
)

REM Set ExecutionPolicy to Bypass only for this process and run the script
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "Setup.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Setup encountered an error.
    pause
)