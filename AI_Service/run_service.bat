@echo off
echo ========================================================
echo   KHOI DONG AI INFERENCE SERVICE (YOLO + ROCA 6DoF)
echo ========================================================
python -m pip install -r requirements.txt
if errorlevel 1 (
    py -m pip install -r requirements.txt
)
python app.py
if errorlevel 1 (
    py app.py
)
pause