@echo off
cd /d "%~dp0"
echo ========================================================
echo   TAI ANH THAT VA TAO DATASET YOLO - IPHONE DETECTION
echo ========================================================
echo.

set "PY=python"
if exist "..\.venv\Scripts\python.exe" (
    set "PY=..\.venv\Scripts\python.exe"
) else if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
)

echo Buoc 1: Kiem tra va cai dat thu vien...
%PY% -m pip install requests Pillow opencv-python numpy tqdm ultralytics
echo.
echo Buoc 2: Tai anh mat sau that tu internet (cac dong iPhone)...
%PY% tools/download_real_dataset.py --max-images 30 --augment 2 --output dataset_real_v1 --merge-with-synthetic
echo.
echo Buoc 3: Train YOLO tren dataset gop...
%PY% train_yolo.py --data dataset_real_v1_merged/data.yaml --epochs 25 --batch 8 --name iphone_real_merged_v1 --output weights/yolo_phone_detect.pt
echo.
echo ========================================================
echo   HOAN TAT! Model da luu tai weights/yolo_phone_detect.pt
echo ========================================================
pause
