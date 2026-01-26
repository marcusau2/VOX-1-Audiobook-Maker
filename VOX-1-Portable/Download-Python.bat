@echo off
REM ============================================
REM Download Embedded Python 3.10.11
REM ============================================

echo ============================================
echo VOX-1 Portable - Python Downloader
echo ============================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if python310 already exists
if exist "python310\python.exe" (
    echo Python 3.10 already downloaded!
    echo.
    echo Next step: Run Setup-Portable.bat
    echo.
    pause
    exit /b 0
)

echo Downloading Python 3.10.11 Embedded (8.9 MB)...
echo This may take a minute...
echo.

REM Download using PowerShell
powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip' -OutFile 'python-3.10.11-embed-amd64.zip'}"

if errorlevel 1 (
    echo.
    echo ERROR: Download failed!
    echo.
    echo Please download manually from:
    echo https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip
    echo.
    echo Then extract and rename to "python310"
    echo.
    pause
    exit /b 1
)

echo.
echo Download complete! Extracting...
echo.

REM Extract using PowerShell
powershell -Command "& {Expand-Archive -Path 'python-3.10.11-embed-amd64.zip' -DestinationPath 'python310' -Force}"

if errorlevel 1 (
    echo.
    echo ERROR: Extraction failed!
    echo Please extract manually.
    echo.
    pause
    exit /b 1
)

REM Clean up zip file
del python-3.10.11-embed-amd64.zip

echo.
echo ============================================
echo SUCCESS! Python 3.10 is ready.
echo ============================================
echo.
echo Next step: Run Setup-Portable.bat
echo.
pause
