@echo off
setlocal
cd /d "%~dp0"

echo Starting Moca-Tris...
".venv\Scripts\python.exe" "tetris.py"

if errorlevel 1 (
    echo.
    echo The game exited with an error. See the message above.
    pause
)
