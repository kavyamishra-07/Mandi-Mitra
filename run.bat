@echo off
cd /d "%~dp0"
echo Step 1 of 2: installing packages (first time takes a few minutes)...
python -m pip install --user -r requirements.txt
if errorlevel 1 goto failed
echo.
echo ==========================================================
echo  Step 2 of 2: starting the server. KEEP THIS WINDOW OPEN.
echo  When you see "Uvicorn running", open http://127.0.0.1:8000
echo ==========================================================
python -m mandi_mitra.server
echo.
echo The server stopped. Copy the text above and send it to Claude.
pause
exit /b
:failed
echo.
echo Install failed. Copy the text above and send it to Claude.
pause
