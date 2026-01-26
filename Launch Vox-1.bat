@echo off
REM ============================================
REM VOX-1 Audiobook Generator Launcher
REM ============================================

REM Change to the script's directory
cd /d "%~dp0"

REM Check if Python 3.10 is available
py -3.10 --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.10 is not installed or not found.
    echo.
    echo Please install Python 3.10.8 from:
    echo https://www.python.org/downloads/release/python-3108/
    echo.
    pause
    exit /b 1
)

REM Launch the GUI without console window
echo Launching VOX-1 Audiobook Generator...
start /B py -3.10 app.py

REM Exit the batch file
exit
