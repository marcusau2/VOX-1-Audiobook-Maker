@echo off
echo ============================================
echo    VOX-1 Audiobook Maker - DEBUG MODE
echo ============================================
echo.
echo This launcher shows detailed debug information.
echo Use this if VOX-1 isn't working properly.
echo.
echo IMPORTANT: Keep this window open while using VOX-1!
echo.
echo ============================================
echo.
cd /d "%~dp0"
echo Current directory: %CD%
echo.
echo Checking Python...
if exist "python310\python.exe" (
    echo [OK] Python found
    python310\python.exe --version
) else (
    echo [ERROR] Python not found at: python310\python.exe
    echo Please run Install-VOX-1.bat
    pause
    exit /b 1
)
echo.
echo Checking app.py...
if exist "app.py" (
    echo [OK] app.py found
) else (
    echo [ERROR] app.py not found
    echo Please run Install-VOX-1.bat
    pause
    exit /b 1
)
echo.
echo Starting VOX-1 with debug output...
echo ============================================
echo.
python310\python.exe app.py
echo.
echo ============================================
echo VOX-1 has stopped.
echo.
if errorlevel 1 (
    echo [ERROR] The app exited with an error code.
    echo Check the output above for error messages.
)
pause
