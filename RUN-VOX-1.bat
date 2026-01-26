@echo off
echo ============================================
echo    VOX-1 Audiobook Maker
echo ============================================
echo.
cd /d "%~dp0"

if not exist "system_python\python.exe" (
    echo ERROR: Python environment not found!
    echo Please run Install-VOX-1.bat first.
    echo.
    pause
    exit /b 1
)

echo Starting VOX-1...
echo.
echo IMPORTANT: Keep this console window open!
echo.

system_python\python.exe app.py

echo.
echo VOX-1 has stopped.
pause
