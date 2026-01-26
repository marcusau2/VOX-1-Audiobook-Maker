@echo off
REM ============================================
REM VOX-1 Audiobook Maker - Installer
REM ============================================
REM
REM This script will:
REM - Download Python 3.10 (embedded)
REM - Download VOX-1 source code from GitHub
REM - Download FFmpeg
REM - Install all dependencies
REM - Set up the launcher
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
echo Total download size: ~2.5 GB
echo Estimated time: 10-15 minutes
echo.
echo Press any key to continue, or CTRL+C to cancel...
pause >nul
echo.

REM Change to script directory
cd /d "%~dp0"

REM ============================================
echo [1/6] Downloading Python 3.10 (~9 MB)...
echo ============================================
echo.

if exist "python310\python.exe" (
    echo Python 3.10 already downloaded.
) else (
    echo Downloading Python 3.10.11 embedded...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.10.11/python-3.10.11-embed-amd64.zip' -OutFile 'python.zip'}"

    if errorlevel 1 (
        echo ERROR: Failed to download Python!
        echo Please check your internet connection.
        pause
        exit /b 1
    )

    echo Extracting Python...
    powershell -Command "& {Expand-Archive -Path 'python.zip' -DestinationPath 'python310' -Force}"
    del python.zip
    echo Done.
)
echo.

REM ============================================
echo [2/6] Configuring Python environment...
echo ============================================
echo.

if exist "python310\python310._pth" (
    copy /Y "python310\python310._pth" "python310\python310._pth.bak" >nul
    (
        echo python310.zip
        echo .
        echo ..
        echo import site
    ) > "python310\python310._pth"
)
echo Done.
echo.

REM ============================================
echo [3/6] Installing pip...
echo ============================================
echo.

if not exist "python310\Scripts\pip.exe" (
    echo Downloading pip installer...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'}"
    python310\python.exe get-pip.py
    del get-pip.py
    echo Done.
) else (
    echo Pip already installed.
)
echo.

REM ============================================
echo [4/6] Downloading VOX-1 source code from GitHub...
echo ============================================
echo.

if exist "app\app.py" (
    echo Source code already downloaded.
    echo.
    choice /C YN /M "Do you want to re-download (update)"
    if errorlevel 2 goto skip_download
    echo.
    echo Re-downloading latest version...
    rmdir /S /Q app 2>nul
)

echo Downloading from GitHub...
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/marcusau2/VOX-1-Audiobook-Maker/archive/refs/heads/main.zip' -OutFile 'vox1-source.zip'}"

if errorlevel 1 (
    echo ERROR: Failed to download source code!
    echo Please check your internet connection.
    pause
    exit /b 1
)

echo Extracting source code...
powershell -Command "& {Expand-Archive -Path 'vox1-source.zip' -DestinationPath 'temp' -Force}"

echo Organizing files...
mkdir app 2>nul
xcopy /E /I /Y "temp\VOX-1-Audiobook-Maker-main\*.py" "app\" >nul
xcopy /E /I /Y "temp\VOX-1-Audiobook-Maker-main\booksmith_module" "app\booksmith_module\" >nul
copy /Y "temp\VOX-1-Audiobook-Maker-main\requirements.txt" "app\requirements.txt" >nul
copy /Y "temp\VOX-1-Audiobook-Maker-main\*.md" "app\" >nul 2>nul

REM Download ComfyUI-Qwen-TTS library
echo Downloading TTS library (ComfyUI-Qwen-TTS)...
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/flybirdxx/ComfyUI-Qwen-TTS/archive/refs/heads/main.zip' -OutFile 'comfyui-tts.zip'}"

if errorlevel 1 (
    echo.
    echo WARNING: Failed to download TTS library!
    echo Trying alternate method...
    echo.
    REM Try without Invoke-WebRequest
    powershell -Command "wget 'https://github.com/flybirdxx/ComfyUI-Qwen-TTS/archive/refs/heads/main.zip' -O 'comfyui-tts.zip'"
)

if not exist "comfyui-tts.zip" (
    echo ERROR: Could not download TTS library!
    echo The app will not work without this.
    echo.
    echo Please check your internet connection and try again.
    pause
    exit /b 1
)

powershell -Command "& {Expand-Archive -Path 'comfyui-tts.zip' -DestinationPath 'temp_tts' -Force}"
xcopy /E /I /Y "temp_tts\ComfyUI-Qwen-TTS-main" "app\ComfyUI-Qwen-TTS\" >nul
rmdir /S /Q temp_tts 2>nul
del comfyui-tts.zip 2>nul

REM Create output directories
mkdir "app\Output" 2>nul
mkdir "app\VOX-Output" 2>nul
mkdir "app\temp_work" 2>nul
mkdir "app\ffmpeg_bundle" 2>nul

REM Cleanup
rmdir /S /Q temp 2>nul
del vox1-source.zip 2>nul
echo Done.

:skip_download
echo.

REM ============================================
echo [5/6] Downloading FFmpeg (~201 MB from GitHub)...
echo ============================================
echo.

if exist "app\ffmpeg_bundle\ffmpeg.exe" (
    echo FFmpeg already installed.
) else (
    echo Downloading FFmpeg from GitHub (fast CDN)...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'ffmpeg.zip'}"

    if errorlevel 1 (
        echo WARNING: FFmpeg download failed!
        echo The app may not work properly without FFmpeg.
        echo You can download manually later.
    ) else (
        echo Extracting FFmpeg...
        powershell -Command "& {Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg_temp' -Force}"

        for /d %%D in (ffmpeg_temp\ffmpeg-*) do (
            copy /Y "%%D\bin\ffmpeg.exe" "app\ffmpeg_bundle\ffmpeg.exe" >nul
            copy /Y "%%D\bin\ffprobe.exe" "app\ffmpeg_bundle\ffprobe.exe" >nul
        )

        rmdir /S /Q ffmpeg_temp 2>nul
        del ffmpeg.zip 2>nul
        echo Done.
    )
)
echo.

REM ============================================
echo [6/6] Installing Python dependencies (~2 GB)...
echo ============================================
echo.
echo This will take 5-10 minutes...
echo Downloading PyTorch, Transformers, and other packages...
echo.

python310\python.exe -m pip install --upgrade pip >nul 2>&1
echo Pip upgraded.
echo.
echo Installing packages (this is the slow part)...
python310\python.exe -m pip install -r app\requirements.txt

if errorlevel 1 (
    echo.
    echo WARNING: Some packages may have failed to install.
    echo.
    echo The launcher files will still be created.
    echo You can run the installer again to retry, or run:
    echo   python310\python.exe -m pip install -r app\requirements.txt
    echo.
    pause
)

REM ============================================
echo Creating launchers and guides...
echo ============================================

REM Create main launcher - RUN-VOX-1.bat (no spaces in filename)
> "RUN-VOX-1.bat" echo @echo off
>>"RUN-VOX-1.bat" echo echo ============================================
>>"RUN-VOX-1.bat" echo echo    VOX-1 Audiobook Maker
>>"RUN-VOX-1.bat" echo echo ============================================
>>"RUN-VOX-1.bat" echo echo.
>>"RUN-VOX-1.bat" echo echo Starting VOX-1...
>>"RUN-VOX-1.bat" echo echo The app will open in your browser.
>>"RUN-VOX-1.bat" echo echo.
>>"RUN-VOX-1.bat" echo echo IMPORTANT: Keep this window open while using VOX-1!
>>"RUN-VOX-1.bat" echo echo            Closing this window will stop the app.
>>"RUN-VOX-1.bat" echo echo.
>>"RUN-VOX-1.bat" echo echo ============================================
>>"RUN-VOX-1.bat" echo echo.
>>"RUN-VOX-1.bat" echo cd /d "%%~dp0"
>>"RUN-VOX-1.bat" echo python310\python.exe app\app.py
>>"RUN-VOX-1.bat" echo echo.
>>"RUN-VOX-1.bat" echo echo VOX-1 has stopped.
>>"RUN-VOX-1.bat" echo pause

REM Create debug launcher
> "Launch-Debug.bat" echo @echo off
>>"Launch-Debug.bat" echo echo Debug Mode - You will see detailed error messages
>>"Launch-Debug.bat" echo echo.
>>"Launch-Debug.bat" echo cd /d "%%~dp0"
>>"Launch-Debug.bat" echo python310\python.exe app\app.py
>>"Launch-Debug.bat" echo echo.
>>"Launch-Debug.bat" echo echo Press any key to close...
>>"Launch-Debug.bat" echo pause

REM Create START HERE guide
(
    echo ==========================================
    echo    VOX-1 AUDIOBOOK MAKER - START HERE
    echo ==========================================
    echo.
    echo CONGRATULATIONS! VOX-1 is installed and ready to use.
    echo.
    echo ==========================================
    echo QUICK START:
    echo ==========================================
    echo.
    echo 1. Double-click: RUN-VOX-1.bat
    echo    ^(The app will open in your browser^)
    echo.
    echo 2. Read the User Guide: USER_GUIDE.txt
    echo    ^(Complete instructions for beginners^)
    echo.
    echo 3. Keep the black console window open
    echo    ^(Closing it will stop VOX-1^)
    echo.
    echo ==========================================
    echo WHAT TO DO FIRST:
    echo ==========================================
    echo.
    echo In the VOX-1 app ^(browser^):
    echo.
    echo 1. Go to "The Lab" tab
    echo    - Create a voice or clone one from audio
    echo    - Click "Save as Master Voice"
    echo.
    echo 2. Go to "Studio" tab
    echo    - Load your saved voice
    echo    - Load a text file ^(TXT or JSON^)
    echo    - Click "Render Audiobook"
    echo.
    echo 3. Find your audiobook in: VOX-Output\ folder
    echo.
    echo ==========================================
    echo FILES IN THIS FOLDER:
    echo ==========================================
    echo.
    echo RUN-VOX-1.bat       - Start the app ^(USE THIS^)
    echo USER_GUIDE.txt      - Full instructions
    echo Launch-Debug.bat    - For troubleshooting
    echo app\                - Application files
    echo VOX-Output\         - Your finished audiobooks
    echo.
    echo ==========================================
    echo NEED HELP?
    echo ==========================================
    echo.
    echo - Read USER_GUIDE.txt for detailed instructions
    echo - Check the activity log in the app for errors
    echo - Visit: https://github.com/marcusau2/VOX-1-Audiobook-Maker
    echo.
    echo ==========================================
    echo.
    echo Ready to create audiobooks? Double-click RUN-VOX-1.bat
    echo.
) > "START_HERE.txt"

REM Copy user guide from app folder to root for easy access
copy /Y "app\USER_GUIDE.md" "USER_GUIDE.txt" >nul 2>nul

echo Done.
echo.

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
echo 1. Read: START_HERE.txt (opening now...)
echo.
echo 2. To launch VOX-1:
echo    Double-click: RUN-VOX-1.bat
echo.
echo 3. For help:
echo    Read: USER_GUIDE.txt
echo.
echo ============================================
echo.
echo The app will open in your web browser.
echo Keep the console window open while using VOX-1!
echo.
echo System Requirements:
echo - NVIDIA GPU with 8GB+ VRAM
echo - Windows 10/11
echo.
echo ============================================
echo.

REM Open START_HERE.txt automatically
start "" "START_HERE.txt"

echo Opening START_HERE.txt...
echo.
pause
