@echo off
echo ============================================
echo    VOX-1 Audiobook Maker
echo ============================================
echo.
echo Starting VOX-1...
echo A desktop window will open shortly.
echo.
echo IMPORTANT: Keep this console window open while using VOX-1!
echo            Closing this window will stop the app.
echo.
echo ============================================
echo.
cd /d "%~dp0"
python310\python.exe app.py
echo.
echo VOX-1 has stopped.
pause
