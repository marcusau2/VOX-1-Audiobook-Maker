@echo off
echo ============================================
echo    VOX-1 Audiobook Maker - DEBUG MODE
echo ============================================
echo.
cd /d "%~dp0"

echo Checking Python environment...
if exist "venv\Scripts\python.exe" (
    echo [OK] Python found in venv
    venv\Scripts\python.exe --version
) else (
    echo [ERROR] Python not found at: venv\Scripts\python.exe
    echo Please run Install-VOX-1.bat
    pause
    exit /b 1
)

echo.
echo Starting VOX-1 with debug output...
echo ============================================
echo.
venv\Scripts\python.exe app.py
echo.
echo ============================================
echo VOX-1 has stopped.
echo.
pause