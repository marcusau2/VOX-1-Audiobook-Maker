@echo off
echo ============================================
echo    VOX-1 Audiobook Maker
echo ============================================
echo.
echo Starting VOX-1...
echo The app will open in your browser.
echo.
echo IMPORTANT: Keep this window open while using VOX-1!
echo            Closing this window will stop the app.
echo.
echo ============================================
echo.
cd /d "%~dp0"
python310\python.exe app\app.py
echo.
echo VOX-1 has stopped.
pause
