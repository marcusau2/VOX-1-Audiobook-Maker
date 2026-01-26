@echo off
setlocal enabledelayedexpansion

REM ============================================
REM VOX-1 Audiobook Maker - Installer
REM ============================================
REM
REM PREREQUISITES:
REM - Download the full repository ZIP from GitHub
REM - Extract it to a folder
REM - Run this installer from that folder
REM
REM This script will:
REM - Download Python 3.10 (full installer with tkinter)
REM - Verify pip
REM - Download FFmpeg
REM - Install all Python dependencies
REM
REM Total download: ~2.5 GB
REM Time required: 10-15 minutes
REM ============================================

echo.
echo ============================================
echo    VOX-1 Audiobook Maker - Installer
echo ============================================
echo.
echo This will install VOX-1 in the current folder:
echo %CD%
echo.
echo Prerequisites: You should have downloaded and extracted
echo the full repository ZIP from GitHub before running this.
echo.
echo Total download size: ~2.5 GB
echo Estimated time: 10-15 minutes
echo.

REM Verify we're in the right directory
echo Checking for required files...
set MISSING_FILES=0

if not exist "app.py" (
    echo   [MISSING] app.py
    set MISSING_FILES=1
)

if not exist "backend.py" (
    echo   [MISSING] backend.py
    set MISSING_FILES=1
)

if not exist "requirements.txt" (
    echo   [MISSING] requirements.txt
    set MISSING_FILES=1
)

if not exist "RUN-VOX-1.bat" (
    echo   [MISSING] RUN-VOX-1.bat
    set MISSING_FILES=1
)

if not exist "booksmith_module" (
    echo   [MISSING] booksmith_module folder
    set MISSING_FILES=1
)

if %MISSING_FILES% EQU 1 (
    echo.
    echo ============================================
    echo ERROR: Missing required files!
    echo ============================================
    echo.
    echo It looks like you're not running this installer from
    echo the extracted repository folder.
    echo.
    echo Please:
    echo 1. Download the repository ZIP from GitHub
    echo 2. Extract it to a folder
    echo 3. Run this Install-VOX-1.bat from that folder
    echo.
    pause
    exit /b 1
)

echo   [OK] app.py
echo   [OK] backend.py
echo   [OK] requirements.txt
echo   [OK] RUN-VOX-1.bat
echo   [OK] booksmith_module
echo.
echo All required files found!
echo.
echo Press any key to continue, or CTRL+C to cancel...
pause >nul
echo.

REM Change to script directory
cd /d "%~dp0"

REM ============================================
echo [Step 1/4] Downloading Python 3.10 (~25 MB)...
echo ============================================
echo.

if exist "python310\python.exe" (
    echo Python 3.10 already installed.
) else (
    echo Downloading Python 3.10.11 (full installer with tkinter)...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe' -OutFile 'python-installer.exe'"

    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ERROR: Failed to download Python!
        echo Please check your internet connection.
        echo.
        pause
        exit /b 1
    )

    echo Installing Python to python310 folder...
    echo This may take 1-2 minutes...
    echo.

    REM Use start /wait to ensure installer completes before continuing
    start /wait "" python-installer.exe /quiet InstallAllUsers=0 PrependPath=0 Include_test=0 TargetDir="%CD%\python310"

    echo.
    echo Verifying Python installation...

    if not exist "python310\python.exe" (
        echo.
        echo ERROR: Python installation failed!
        echo python.exe not found in python310 folder.
        echo.
        echo Possible causes:
        echo - Installation was cancelled
        echo - Insufficient disk space
        echo - Antivirus blocked the installation
        echo.
        pause
        exit /b 1
    )

    del python-installer.exe 2>nul
    echo Python installed successfully!
)
echo.

REM ============================================
echo [Step 2/4] Verifying Python and tkinter...
echo ============================================
echo.

echo Checking Python version...
python310\python.exe --version

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not working correctly!
    pause
    exit /b 1
)

echo Checking tkinter module...
python310\python.exe -c "import tkinter; print('tkinter OK')"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: tkinter module is missing!
    echo This should not happen with the full Python installer.
    echo.
    pause
    exit /b 1
)

echo Python and tkinter are ready!
echo.

REM ============================================
echo [Step 3/4] Verifying pip installation...
echo ============================================
echo.

REM Full Python installer includes pip
python310\python.exe -m pip --version

if %ERRORLEVEL% NEQ 0 (
    echo Pip not found, installing...
    powershell -Command "Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'"
    python310\python.exe get-pip.py
    del get-pip.py
)

echo Pip is ready!
echo.

REM ============================================
echo [Step 4/4] Downloading FFmpeg (~201 MB)...
echo ============================================
echo.

REM Create output directories
mkdir "Output" 2>nul
mkdir "VOX-Output" 2>nul
mkdir "temp_work" 2>nul
mkdir "ffmpeg_bundle" 2>nul

if exist "ffmpeg_bundle\ffmpeg.exe" (
    echo FFmpeg already installed.
) else (
    echo Downloading FFmpeg from GitHub...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'ffmpeg.zip'"

    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo WARNING: FFmpeg download failed!
        echo The app may not work properly without FFmpeg.
        echo You can download it manually later.
        echo.
    ) else (
        echo Extracting FFmpeg...
        powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg_temp' -Force"

        if %ERRORLEVEL% NEQ 0 (
            echo WARNING: Failed to extract FFmpeg.
        ) else (
            REM Find and copy ffmpeg.exe and ffprobe.exe
            for /d %%D in (ffmpeg_temp\ffmpeg-*) do (
                if exist "%%D\bin\ffmpeg.exe" (
                    copy /Y "%%D\bin\ffmpeg.exe" "ffmpeg_bundle\ffmpeg.exe" >nul
                    copy /Y "%%D\bin\ffprobe.exe" "ffmpeg_bundle\ffprobe.exe" >nul
                )
            )
            echo FFmpeg installed successfully.
        )

        rmdir /S /Q ffmpeg_temp 2>nul
        del ffmpeg.zip 2>nul
    )
)
echo.

REM ============================================
echo [Step 5/5] Installing Python dependencies (~2 GB)...
echo ============================================
echo.
echo This will take 5-10 minutes...
echo Downloading PyTorch, Transformers, customtkinter, qwen-tts, and other packages...
echo.
echo NOTE: You will see the installation progress below.
echo       This is normal and expected.
echo.

echo Upgrading pip...
python310\python.exe -m pip install --upgrade pip

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo WARNING: Failed to upgrade pip, but continuing anyway...
    echo.
)

echo.
echo Installing packages from requirements.txt...
echo This will install in the correct order to avoid conflicts.
echo.
echo ============================================
python310\python.exe -m pip install -r requirements.txt
echo ============================================
echo.

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ============================================
    echo WARNING: Some packages may have failed to install!
    echo ============================================
    echo.
    echo The installation encountered errors. Common causes:
    echo   - Network connection issues
    echo   - Incompatible package versions
    echo   - Missing system dependencies
    echo.
    echo You can try to fix this by running:
    echo   python310\python.exe -m pip install -r requirements.txt
    echo.
    echo Or install individual packages manually.
    echo.
    pause
) else (
    echo.
    echo ============================================
    echo All packages installed successfully!
    echo ============================================
    echo.
)

REM ============================================
echo.
echo ============================================
echo    INSTALLATION COMPLETE!
echo ============================================
echo.
echo VOX-1 has been installed in:
echo %CD%
echo.
echo ============================================
echo NEXT STEPS:
echo ============================================
echo.
echo 1. To launch VOX-1:
echo    Double-click: RUN-VOX-1.bat
echo.
echo 2. For help and documentation:
echo    Read: USER_GUIDE.md
echo    Read: START_HERE.txt
echo.
echo ============================================
echo.
echo A desktop window will open when you run VOX-1.
echo Keep the console window open while using the app!
echo.
echo System Requirements:
echo - NVIDIA GPU with 8GB+ VRAM (required)
echo - Windows 10/11
echo.
echo ============================================
echo.

REM Open START_HERE.txt if it exists
if exist "START_HERE.txt" (
    echo Opening START_HERE.txt...
    start "" "START_HERE.txt"
    echo.
)

echo Installation complete!
echo.
pause
