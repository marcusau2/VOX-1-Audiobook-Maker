@echo off
echo ============================================
echo    VOX-1 Audiobook Maker - DEBUG MODE
echo ============================================
echo.
cd /d "%~dp0"

echo Checking Python environment...
if exist "system_python\python.exe" (
    echo [OK] Python found in system_python
    system_python\python.exe --version
) else (
    echo [ERROR] Python not found at: system_python\python.exe
    echo Please run Install-VOX-1.bat
    pause
    exit /b 1
)

echo.
echo Starting VOX-1 with debug output...
echo ============================================
echo.
system_python\python.exe app.py
echo.
echo ============================================
echo VOX-1 has stopped.
echo.
pause
