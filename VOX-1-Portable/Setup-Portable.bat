@echo off
REM ============================================
REM VOX-1 Portable Setup Script
REM ============================================

echo ============================================
echo VOX-1 Portable Setup
echo ============================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is downloaded
if not exist "python310\python.exe" (
    echo ERROR: Python 3.10 not found!
    echo.
    echo Please run Download-Python.bat first.
    echo.
    pause
    exit /b 1
)

echo [1/6] Python 3.10 found
echo.

REM Enable pip in embedded Python (uncomment python310._pth)
echo [2/6] Configuring embedded Python...
if exist "python310\python310._pth" (
    REM Backup original
    copy /Y "python310\python310._pth" "python310\python310._pth.bak" >nul

    REM Create new _pth without import site commented
    (
        echo python310.zip
        echo .
        echo ..
        echo import site
    ) > "python310\python310._pth"
)
echo Done.
echo.

REM Download get-pip.py if pip not present
if not exist "python310\Scripts\pip.exe" (
    echo [3/6] Installing pip...
    powershell -Command "& {Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile 'get-pip.py'}"
    python310\python.exe get-pip.py
    del get-pip.py
    echo Done.
    echo.
) else (
    echo [3/6] Pip already installed
    echo.
)

REM Download application files from GitHub
echo [4/6] Downloading application files from GitHub...
echo This may take a minute...
echo.

REM GitHub repository info
set GITHUB_USER=marcusau2
set GITHUB_REPO=VOX-1-Audiobook-Maker
set GITHUB_BRANCH=main

REM Download repository as ZIP
powershell -Command "& {Invoke-WebRequest -Uri 'https://github.com/%GITHUB_USER%/%GITHUB_REPO%/archive/refs/heads/%GITHUB_BRANCH%.zip' -OutFile 'repo.zip'}"

if errorlevel 1 (
    echo.
    echo ERROR: Failed to download from GitHub!
    echo.
    echo Please check:
    echo 1. Internet connection is working
    echo 2. GitHub repository is accessible
    echo 3. Repository is set to public or you have access
    echo.
    echo If repository is private, you need to:
    echo - Make it public temporarily, OR
    echo - Download manually and extract to "app" folder
    echo.
    pause
    exit /b 1
)

REM Extract ZIP
echo Extracting files...
powershell -Command "& {Expand-Archive -Path 'repo.zip' -DestinationPath 'temp_extract' -Force}"

REM Copy files from extracted repo to app folder
echo Copying application files...
xcopy /E /I /Y "temp_extract\%GITHUB_REPO%-%GITHUB_BRANCH%\*.py" "app\" >nul
xcopy /E /I /Y "temp_extract\%GITHUB_REPO%-%GITHUB_BRANCH%\booksmith_module" "app\booksmith_module\" >nul
mkdir "app\ffmpeg_bundle" 2>nul
xcopy /E /I /Y "temp_extract\%GITHUB_REPO%-%GITHUB_BRANCH%\ComfyUI-Qwen-TTS" "app\ComfyUI-Qwen-TTS\" >nul
copy /Y "temp_extract\%GITHUB_REPO%-%GITHUB_BRANCH%\requirements.txt" "app\requirements.txt" >nul
copy /Y "temp_extract\%GITHUB_REPO%-%GITHUB_BRANCH%\user_settings.json" "app\user_settings.json" >nul 2>nul
copy /Y "temp_extract\%GITHUB_REPO%-%GITHUB_BRANCH%\*.json" "app\" >nul 2>nul

REM Copy documentation
copy /Y "temp_extract\%GITHUB_REPO%-%GITHUB_BRANCH%\README.md" "app\README.md" >nul 2>nul
copy /Y "temp_extract\%GITHUB_REPO%-%GITHUB_BRANCH%\MANUAL_INSTALL.md" "app\MANUAL_INSTALL.md" >nul 2>nul
copy /Y "temp_extract\%GITHUB_REPO%-%GITHUB_BRANCH%\*.md" "app\" >nul 2>nul

REM Create output directories
mkdir "app\Output" 2>nul
mkdir "app\VOX-Output" 2>nul
mkdir "app\temp_work" 2>nul

REM Cleanup
rmdir /S /Q "temp_extract" 2>nul
del repo.zip 2>nul

echo Done.
echo.

REM Download FFmpeg
echo [5/7] Downloading FFmpeg (~101 MB)...
echo This may take a minute...
echo.

if not exist "app\ffmpeg_bundle\ffmpeg.exe" (
    REM Download FFmpeg essentials build
    powershell -Command "& {Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip'}"

    if errorlevel 1 (
        echo.
        echo WARNING: FFmpeg download failed!
        echo The app may not work properly without FFmpeg.
        echo.
        echo You can download manually from:
        echo https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip
        echo Extract and place ffmpeg.exe and ffprobe.exe in app\ffmpeg_bundle\
        echo.
    ) else (
        echo Extracting FFmpeg...
        powershell -Command "& {Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg_temp' -Force}"

        REM Find and copy ffmpeg.exe and ffprobe.exe from the extracted folder
        for /d %%D in (ffmpeg_temp\ffmpeg-*) do (
            copy /Y "%%D\bin\ffmpeg.exe" "app\ffmpeg_bundle\ffmpeg.exe" >nul
            copy /Y "%%D\bin\ffprobe.exe" "app\ffmpeg_bundle\ffprobe.exe" >nul
        )

        REM Cleanup
        rmdir /S /Q "ffmpeg_temp" 2>nul
        del ffmpeg.zip 2>nul

        echo Done.
    )
) else (
    echo FFmpeg already installed.
)
echo.

REM Install dependencies
echo [6/7] Installing dependencies (this will take 5-10 minutes)...
echo Please be patient, downloading PyTorch and other large packages...
echo.

python310\python.exe -m pip install --upgrade pip
python310\python.exe -m pip install -r app\requirements.txt

if errorlevel 1 (
    echo.
    echo WARNING: Some packages may have failed to install.
    echo Try running this again, or install manually:
    echo   python310\python.exe -m pip install -r app\requirements.txt
    echo.
)

echo.
echo [7/7] Final setup...
echo.

REM Create a batch file for easy launching
(
    echo @echo off
    echo cd /d "%%~dp0app"
    echo ..\python310\python.exe app.py
) > "Launch-VOX-1-Portable.bat"

echo ============================================
echo SETUP COMPLETE!
echo ============================================
echo.
echo To launch VOX-1:
echo   Double-click: Launch VOX-1 Portable.vbs
echo   or: Launch-VOX-1-Portable.bat
echo.
echo The portable version is ready to use!
echo You can copy the entire VOX-1-Portable folder
echo to any Windows PC and it will work.
echo.
pause
