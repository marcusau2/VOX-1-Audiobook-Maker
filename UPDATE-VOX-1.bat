@echo off
REM ====================================================================
REM VOX-1 Audiobook Maker - UPDATE SCRIPT
REM ====================================================================
REM This script updates VOX-1 to the latest version from GitHub
REM ====================================================================

title VOX-1 Update Script
color 0A

echo.
echo ========================================
echo    VOX-1 UPDATE SCRIPT
echo ========================================
echo.

REM Check if git is available
where git >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [X] Git is not installed on your system.
    echo.
    echo You have two options to update:
    echo.
    echo OPTION 1: Install Git and use auto-update
    echo ------------------------------------------
    echo 1. Download Git from: https://git-scm.com/download/win
    echo 2. Install Git with default settings
    echo 3. Run this script again
    echo.
    echo OPTION 2: Manual update (preserves your data)
    echo ----------------------------------------------
    echo 1. Back up these folders (contains your work):
    echo    - Output/
    echo    - VOX-Output/
    echo    - user_settings.json
    echo    - models/ (optional, but saves 8GB re-download)
    echo.
    echo 2. Download latest ZIP from:
    echo    https://github.com/marcusau2/VOX-1-Audiobook-Maker
    echo.
    echo 3. Extract the new ZIP to a temporary location
    echo.
    echo 4. Copy your backed-up folders to the new location
    echo.
    echo 5. Run Install-VOX-1.bat in the new location
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

REM Check if this is a git repository
if not exist ".git" (
    echo [X] This is not a Git repository.
    echo.
    echo It looks like you downloaded VOX-1 as a ZIP file.
    echo To enable auto-updates, you need to clone the repository.
    echo.
    echo HOW TO SWITCH TO GIT-BASED INSTALLATION:
    echo -----------------------------------------
    echo.
    echo 1. Back up these folders (contains your work):
    echo    - Output/
    echo    - VOX-Output/
    echo    - user_settings.json
    echo    - models/ (optional, but saves 8GB re-download)
    echo.
    echo 2. Delete this VOX-1 folder
    echo.
    echo 3. Open Command Prompt and run:
    echo    git clone https://github.com/marcusau2/VOX-1-Audiobook-Maker.git
    echo.
    echo 4. Copy your backed-up folders to the new location
    echo.
    echo 5. Run Install-VOX-1.bat
    echo.
    echo 6. Future updates will be automatic with this script!
    echo.
    echo Press any key to exit...
    pause >nul
    exit /b 1
)

REM At this point, we have git and this is a git repository
echo [OK] Git found: Checking for updates...
echo.

REM Check current branch
for /f "tokens=*" %%i in ('git rev-parse --abbrev-ref HEAD') do set CURRENT_BRANCH=%%i
echo Current branch: %CURRENT_BRANCH%

REM Check if there are local changes
git diff-index --quiet HEAD --
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] WARNING: You have local changes that haven't been committed.
    echo.
    echo These files have been modified:
    git status --short
    echo.
    echo Your changes will be preserved, but updating may require manual merge.
    echo.
    set /p CONTINUE="Continue with update? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        echo Update cancelled.
        pause
        exit /b 0
    )
)

echo.
echo Fetching latest updates from GitHub...
git fetch origin

REM Check if remote has updates
for /f %%i in ('git rev-parse HEAD') do set LOCAL_COMMIT=%%i
for /f %%i in ('git rev-parse origin/%CURRENT_BRANCH%') do set REMOTE_COMMIT=%%i

if "%LOCAL_COMMIT%"=="%REMOTE_COMMIT%" (
    echo.
    echo [OK] You are already on the latest version!
    echo     No updates available.
    echo.
    pause
    exit /b 0
)

echo.
echo [!] Updates available!
echo.
echo Current version:  %LOCAL_COMMIT:~0,7%
echo Latest version:   %REMOTE_COMMIT:~0,7%
echo.
echo Changelog:
echo ----------
git log --oneline %LOCAL_COMMIT%..%REMOTE_COMMIT%
echo.

set /p CONFIRM="Apply updates? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Update cancelled.
    pause
    exit /b 0
)

echo.
echo Applying updates...
git pull origin %CURRENT_BRANCH%

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] Update failed! There may be conflicts.
    echo.
    echo Please resolve conflicts manually or contact support.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo    UPDATE SUCCESSFUL!
echo ========================================
echo.
echo VOX-1 has been updated to the latest version.
echo.
echo IMPORTANT: Check if new dependencies were added:
echo - If requirements.txt changed, run: Install-VOX-1.bat
echo - If only code changed, just restart the app
echo.
echo Recent changes:
git log -3 --pretty=format:"  - %%s" HEAD
echo.
echo.
echo Press any key to exit...
pause >nul
