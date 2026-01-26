@echo off
cd /d "%~dp0"
echo ========================================================
echo Launching VOX-1 Update...
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
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "Update.ps1"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Update encountered an error.
    pause
)
