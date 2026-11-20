@echo off
cd /d "%~dp0"
echo ========================================================
echo   KHOI DONG AI INFERENCE SERVICE (YOLO + ROCA 6DoF)
echo   Cong: http://localhost:5001
echo ========================================================

set "PY=python"
if exist "..\.venv\Scripts\python.exe" (
    set "PY=..\.venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
)

echo Dang khoi dong bang: %PY%
%PY% app.py
if errorlevel 1 (
    pause
)
