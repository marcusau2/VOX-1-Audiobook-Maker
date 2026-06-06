@echo off
setlocal enabledelayedexpansion

echo ============================================
echo    VOX-1 Audiobook Maker
echo ============================================
echo.
cd /d "%~dp0"

:: Try system_python first (portable install)
if exist "system_python\python.exe" (
    set PYTHON=system_python\python.exe
    goto :run
)

:: Fall back to scoop Python 3.12
if exist "C:\Users\marcj\scoop\apps\python312\current\python.exe" (
    set PYTHON=C:\Users\marcj\scoop\apps\python312\current\python.exe
    goto :run
)

:: Fall back to PATH python
where python >nul 2>&1
if !errorlevel! equ 0 (
    set PYTHON=python
    goto :run
)

echo ERROR: Python not found!
echo Please run Install-VOX-1.bat first.
echo.
pause
exit /b 1

:run
echo Starting VOX-1 using !PYTHON!...
echo.
echo IMPORTANT: Keep this console window open!
echo.

!PYTHON! app.py

echo.
echo VOX-1 has stopped.
pause
