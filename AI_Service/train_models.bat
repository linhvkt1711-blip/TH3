@echo off
echo ========================================================
echo   HUAN LUYEN MODEL YOLO NHAN DIEN CAC DONG IPHONE
echo ========================================================
echo.
echo 1. Huan luyen nhanh (15 epochs - Khuyen nghi cho CPU)
echo 2. Huan luyen sau (35 epochs - Do chinh xac cao)
echo 3. Tao lai toan bo bo du lieu Dataset
echo.
set /p choice="Chon che do (1/2/3) [Mac dinh: 1]: "

if "%choice%"=="2" (
    python train_yolo.py --epochs 35 --batch 8 --imgsz 416
) else if "%choice%"=="3" (
    python tools\generate_dataset.py
) else (
    python train_yolo.py --epochs 15 --batch 8 --imgsz 416
)

echo.
echo ========================================================
echo   DA CAP NHAT FILE WEIGHTS: weights/yolo_phone_detect.pt
echo ========================================================
pause
