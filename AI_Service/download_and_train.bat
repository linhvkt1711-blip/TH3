@echo off
echo ========================================================
echo   TAI ANH THAT VA TAO DATASET YOLO - IPHONE DETECTION
echo ========================================================
echo.
echo Buoc 1: Cai dat thu vien can thiet...
python -m pip install requests Pillow opencv-python numpy tqdm ultralytics
echo.
echo Buoc 2: Tai anh that tu internet (50 anh moi dong iPhone)...
python tools/download_real_dataset.py --max-images 50 --augment 3 --output dataset_real_v1 --merge-with-synthetic
echo.
echo Buoc 3: Train YOLO tren dataset gop (synthetic + real)...
python train_yolo.py --data dataset_real_v1_merged/data.yaml --epochs 50 --batch 8 --name iphone_real_merged_v1 --output weights/yolo_phone_detect.pt
echo.
echo ========================================================
echo   HOAN TAT! Model da luu tai weights/yolo_phone_detect.pt
echo ========================================================
pause
