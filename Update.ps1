# ============================================================================
# VOX-1 Audiobook Maker - Update Script
# ============================================================================
# This script updates VOX-1 to the latest version from GitHub
# ============================================================================

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$RootDir = $PSScriptRoot
$PythonSystemDir = Join-Path $RootDir "system_python"
$PythonExe = Join-Path $PythonSystemDir "python.exe"

# Helper: Check if command exists
function Test-Command {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

Clear-Host
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "    VOX-1 UPDATE SCRIPT" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# 1. CHECK IF GIT IS INSTALLED
if (-not (Test-Command "git")) {
    Write-Host "[X] Git is not installed on your system." -ForegroundColor Red
    Write-Host ""
    Write-Host "You have two options to update:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "OPTION 1: Install Git and use auto-update" -ForegroundColor Green
    Write-Host "------------------------------------------"
    Write-Host "1. Download Git from: https://git-scm.com/download/win"
    Write-Host "2. Install Git with default settings"
    Write-Host "3. Run this script again"
    Write-Host ""
    Write-Host "OPTION 2: Manual update (preserves your data)" -ForegroundColor Green
    Write-Host "----------------------------------------------"
    Write-Host "1. Back up these folders (contains your work):"
    Write-Host "   - Output/"
    Write-Host "   - VOX-Output/"
    Write-Host "   - user_settings.json"
    Write-Host "   - models/ (optional, but saves 8GB re-download)"
    Write-Host ""
    Write-Host "2. Download latest ZIP from:"
    Write-Host "   https://github.com/marcusau2/VOX-1-Audiobook-Maker"
    Write-Host ""
    Write-Host "3. Extract the new ZIP to a temporary location"
    Write-Host ""
    Write-Host "4. Copy your backed-up folders to the new location"
    Write-Host ""
    Write-Host "5. Run Install-VOX-1.bat in the new location"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# 2. CHECK IF THIS IS A GIT REPOSITORY
$GitDir = Join-Path $RootDir ".git"
if (-not (Test-Path $GitDir)) {
    Write-Host "[X] This is not a Git repository." -ForegroundColor Red
    Write-Host ""
    Write-Host "It looks like you downloaded VOX-1 as a ZIP file." -ForegroundColor Yellow
    Write-Host "To enable auto-updates, you need to clone the repository." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "HOW TO SWITCH TO GIT-BASED INSTALLATION:" -ForegroundColor Green
    Write-Host "-----------------------------------------"
    Write-Host ""
    Write-Host "1. Back up these folders (contains your work):"
    Write-Host "   - Output/"
    Write-Host "   - VOX-Output/"
    Write-Host "   - user_settings.json"
    Write-Host "   - models/ (optional, but saves 8GB re-download)"
    Write-Host ""
    Write-Host "2. Delete this VOX-1 folder"
    Write-Host ""
    Write-Host "3. Open Command Prompt or PowerShell and run:"
    Write-Host "   git clone https://github.com/marcusau2/VOX-1-Audiobook-Maker.git"
    Write-Host ""
    Write-Host "4. Copy your backed-up folders to the new location"
    Write-Host ""
    Write-Host "5. Run Install-VOX-1.bat"
    Write-Host ""
    Write-Host "6. Future updates will be automatic with this script!"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# 3. CHECK CURRENT STATUS
Write-Host "[OK] Git found: Checking for updates..." -ForegroundColor Green
Write-Host ""

Push-Location $RootDir
try {
    $CurrentBranch = git rev-parse --abbrev-ref HEAD
    Write-Host "Current branch: $CurrentBranch" -ForegroundColor Cyan

    # Check for local changes
    git diff-index --quiet HEAD 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[!] WARNING: You have local changes that haven't been committed." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "These files have been modified:" -ForegroundColor Yellow
        git status --short
        Write-Host ""
        Write-Host "Your changes will be preserved, but updating may require manual merge." -ForegroundColor Yellow
        Write-Host ""
        $Continue = Read-Host "Continue with update? (y/n)"
        if ($Continue -ne "y" -and $Continue -ne "Y") {
            Write-Host "Update cancelled." -ForegroundColor Yellow
            Read-Host "Press Enter to exit"
            exit 0
        }
    }

    # 4. FETCH UPDATES FROM GITHUB
    Write-Host ""
    Write-Host "Fetching latest updates from GitHub..." -ForegroundColor Cyan
    git fetch origin

    # 5. CHECK IF UPDATES ARE AVAILABLE
    $LocalCommit = git rev-parse HEAD
    $RemoteCommit = git rev-parse "origin/$CurrentBranch"

    if ($LocalCommit -eq $RemoteCommit) {
        Write-Host ""
        Write-Host "[OK] You are already on the latest version!" -ForegroundColor Green
        Write-Host "     No updates available." -ForegroundColor Green
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 0
    }

    # 6. SHOW CHANGELOG
    Write-Host ""
    Write-Host "[!] Updates available!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Current version:  $($LocalCommit.Substring(0,7))" -ForegroundColor Cyan
    Write-Host "Latest version:   $($RemoteCommit.Substring(0,7))" -ForegroundColor Green
    Write-Host ""
    Write-Host "Changelog:" -ForegroundColor Yellow
    Write-Host "----------"
    git log --oneline "$LocalCommit..$RemoteCommit"
    Write-Host ""

    # Check if requirements.txt will change
    $RequirementsChanged = $false
    $ChangedFiles = git diff --name-only "$LocalCommit..$RemoteCommit"
    if ($ChangedFiles -match "requirements.txt") {
        $RequirementsChanged = $true
        Write-Host "[!] requirements.txt has changed - dependencies will be reinstalled" -ForegroundColor Yellow
        Write-Host ""
    }

    # 7. ASK FOR CONFIRMATION
    $Confirm = Read-Host "Apply updates? (y/n)"
    if ($Confirm -ne "y" -and $Confirm -ne "Y") {
        Write-Host "Update cancelled." -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 0
    }

    # 8. APPLY UPDATES
    Write-Host ""
    Write-Host "Applying updates..." -ForegroundColor Cyan
    git pull origin $CurrentBranch

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "[X] Update failed! There may be conflicts." -ForegroundColor Red
        Write-Host ""
        Write-Host "Please resolve conflicts manually or contact support." -ForegroundColor Red
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }

    # 9. REINSTALL DEPENDENCIES IF NEEDED
    if ($RequirementsChanged) {
        Write-Host ""
        Write-Host "============================================" -ForegroundColor Yellow
        Write-Host "    REINSTALLING DEPENDENCIES" -ForegroundColor Yellow
        Write-Host "============================================" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "requirements.txt has changed. Updating Python packages..." -ForegroundColor Cyan
        Write-Host "This may take a few minutes..." -ForegroundColor Cyan
        Write-Host ""

        if (-not (Test-Path $PythonExe)) {
            Write-Host "[!] Python not found at: $PythonExe" -ForegroundColor Yellow
            Write-Host "    Please run Install-VOX-1.bat to complete the update" -ForegroundColor Yellow
        } else {
            # Upgrade pip first
            & $PythonExe -m pip install --upgrade pip setuptools wheel --no-warn-script-location

            # Install updated requirements
            & $PythonExe -m pip install -r requirements.txt --no-build-isolation

            if ($LASTEXITCODE -ne 0) {
                Write-Host ""
                Write-Host "[X] Failed to install some dependencies." -ForegroundColor Red
                Write-Host "    Please run Install-VOX-1.bat to fix this" -ForegroundColor Yellow
                Write-Host ""
                Read-Host "Press Enter to exit"
                exit 1
            }

            Write-Host ""
            Write-Host "[OK] Dependencies updated successfully!" -ForegroundColor Green
        }
    }

    # 10. SUCCESS MESSAGE
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "    UPDATE SUCCESSFUL!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "VOX-1 has been updated to the latest version." -ForegroundColor Green
    Write-Host ""

    if ($RequirementsChanged) {
        Write-Host "Dependencies were automatically updated." -ForegroundColor Cyan
        Write-Host ""
    }

    Write-Host "Recent changes:" -ForegroundColor Yellow
    git log -3 --pretty=format:"  - %s" HEAD
    Write-Host ""
    Write-Host ""
    Write-Host "You can now restart the app with RUN-VOX-1.bat" -ForegroundColor Cyan
    Write-Host ""

} finally {
    Pop-Location
}

Read-Host "Press Enter to exit"
