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
xcopy /E /I /Y "temp\VOX-1-Audiobook-Maker-main\ComfyUI-Qwen-TTS" "app\ComfyUI-Qwen-TTS\" >nul
copy /Y "temp\VOX-1-Audiobook-Maker-main\requirements.txt" "app\requirements.txt" >nul
copy /Y "temp\VOX-1-Audiobook-Maker-main\*.md" "app\" >nul 2>nul

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

python310\python.exe -m pip install --upgrade pip
python310\python.exe -m pip install -r app\requirements.txt

if errorlevel 1 (
    echo.
    echo WARNING: Some packages may have failed to install.
    echo Try running this script again, or check your internet connection.
    echo.
)

REM ============================================
echo Creating launcher...
echo ============================================

REM Create VBS launcher
(
    echo Set WshShell = CreateObject^("WScript.Shell"^)
    echo WshShell.CurrentDirectory = CreateObject^("Scripting.FileSystemObject"^).GetParentFolderName^(WScript.ScriptFullName^)
    echo WshShell.Run "python310\python.exe app\app.py", 0, False
) > "Launch-VOX-1.vbs"

REM Create BAT launcher for debugging
(
    echo @echo off
    echo cd /d "%%~dp0"
    echo python310\python.exe app\app.py
    echo pause
) > "Launch-VOX-1-Debug.bat"

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
echo To launch VOX-1:
echo   Double-click: Launch-VOX-1.vbs
echo.
echo For debugging (shows console):
echo   Double-click: Launch-VOX-1-Debug.bat
echo.
echo The app will open in your web browser.
echo.
echo System Requirements:
echo - NVIDIA GPU with 8GB+ VRAM
echo - Windows 10/11
echo.
echo For help, see: app\README.md
echo.
pause
