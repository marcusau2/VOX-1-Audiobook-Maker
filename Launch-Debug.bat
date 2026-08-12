@echo off
setlocal enabledelayedexpansion

echo ============================================
echo    VOX-1 Audiobook Maker - DEBUG MODE
echo ============================================
echo.
cd /d "%~dp0"

:: Isolate from any inherited PYTHONPATH (e.g. other Python venvs on this
:: machine) so the app always uses Python's own site-packages. The backend
:: also self-sanitizes, this is defense in depth.
set PYTHONPATH=

echo Checking Python environment...
if exist "system_python\python.exe" (
    echo [OK] Python found in system_python
    set PYTHON=system_python\python.exe
) else if exist "C:\Users\marcj\scoop\apps\python312\current\python.exe" (
    echo [OK] Python found: scoop Python 3.12
    set PYTHON=C:\Users\marcj\scoop\apps\python312\current\python.exe
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        echo [OK] Python found in PATH
        set PYTHON=python
    ) else (
        echo [ERROR] Python not found!
        echo Please run Install-VOX-1.bat
        pause
        exit /b 1
    )
)

!PYTHON! --version

echo.
echo Starting VOX-1 with debug output...
echo ============================================
echo.
!PYTHON! app.py
echo.
echo ============================================
echo VOX-1 has stopped.
echo.
pause
