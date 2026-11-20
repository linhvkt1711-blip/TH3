@echo off
cd /d "%~dp0"
echo ========================================================
echo   HUAN LUYEN MODEL YOLO NHAN DIEN CAC DONG IPHONE
echo ========================================================
echo.

set "PY=python"
if exist "..\.venv\Scripts\python.exe" (
    set "PY=..\.venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
)

echo 1. Huan luyen tu bo anh that nguoi dung vua upload (Khuyen nghi - 10 epochs)
echo 2. Tao bo du lieu tong hop toan dien va huan luyen
echo 3. Huan luyen nhanh 5 epochs
echo.
set /p choice="Chon che do (1/2/3) [Mac dinh: 1]: "

if "%choice%"=="2" (
    echo Dang tao dataset tong hop cac dong iPhone...
    %PY% tools\generate_dataset.py
    %PY% train_yolo.py --epochs 15 --batch 8 --imgsz 320
) else if "%choice%"=="3" (
    %PY% tools\train_from_user_zip.py 5
) else (
    %PY% tools\train_from_user_zip.py 10
)

echo.
echo ========================================================
echo   DA CAP NHAT FILE WEIGHTS: weights/yolo_phone_detect.pt
echo ========================================================
pause
