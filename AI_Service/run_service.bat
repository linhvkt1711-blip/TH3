@echo off
echo ========================================================
echo   KHOI DONG AI INFERENCE SERVICE (YOLO + ROCA 6DoF)
echo ========================================================
py -3.11 -m pip install -r requirements.txt
if errorlevel 1 (
    echo Khong cai duoc thu vien cho Python 3.11.
    pause
    exit /b 1
)
py -3.11 app.py
pause
