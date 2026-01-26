@echo off
echo ============================================
echo    VOX-1 Debug Mode
echo ============================================
echo.
echo You will see detailed error messages here.
echo Keep this window open to see what happens.
echo.
cd /d "%~dp0"
python310\python.exe app\app.py
echo.
echo.
echo VOX-1 has stopped.
echo Press any key to close...
pause
