# AI_Service/train_yolo.py
"""
Script huấn luyện mô hình YOLOv8 nhận diện chính xác các dòng iPhone và điện thoại.
Sau khi huấn luyện thành công, file weights sẽ được tự động lưu vào AI_Service/weights/yolo_phone_detect.pt
để hệ thống 3D Try-on Studio sử dụng trực tiếp khi quét camera.
"""

import os
import shutil
import argparse
from ultralytics import YOLO
import torch

def train_phone_detector(
    data_yaml=None,
    base_model="weights/yolov8n.pt",
    output_weights="weights/yolo_phone_detect.pt",
    epochs=20,
    batch_size=8,
    imgsz=640,
    device=None,
    run_name="iphone_detect"
):
    service_dir = os.path.dirname(os.path.abspath(__file__))

    if data_yaml is None:
        data_yaml = os.path.join(service_dir, "dataset", "data.yaml")

    train_images = os.path.join(service_dir, "dataset", "images", "train")
    if not os.path.exists(data_yaml) or not os.path.isdir(train_images) or not os.listdir(train_images):
        print(f"Chưa tìm thấy {data_yaml}. Đang tiến hành tạo bộ dữ liệu tự động...")
        from tools.generate_dataset import build_yolo_dataset
        dataset_dir = os.path.join(service_dir, "dataset")
        build_yolo_dataset(dataset_dir, samples_per_class=35)

    base_weights_path = os.path.join(service_dir, base_model)
    if not os.path.exists(base_weights_path):
        base_weights_path = "yolov8n.pt" # Sẽ tự động tải nếu chưa có

    if device is None:
        device = "cuda:0" if torch.cuda.is_available() else "cpu"

    print(f"\n=======================================================")
    print(f" Khởi động huấn luyện YOLOv8 nhận diện điện thoại")
    print(f" -> Dữ liệu: {data_yaml}")
    print(f" -> Mô hình gốc: {base_weights_path}")
    print(f" -> Số Epochs: {epochs}")
    print(f" -> Batch size: {batch_size}")
    print(f" -> Kích thước ảnh: {imgsz}")
    print(f" -> Thiết bị: {device}")
    print(f"=======================================================\n")

    model = YOLO(base_weights_path)

    # Huấn luyện mô hình
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        device=device,
        workers=0, # Phù hợp cho Windows
        optimizer="AdamW",
        lr0=0.002,
        augment=True,
        flipud=0.0, # Điện thoại không nên lộn ngược đầu thường xuyên
        fliplr=0.5, # Lật gương trái phải phù hợp với camera trước/sau
        project=os.path.join(service_dir, "runs"),
        name=run_name,
        exist_ok=True,
        verbose=True
    )

    # Lấy đường dẫn file best.pt
    best_pt = os.path.join(service_dir, "runs", run_name, "weights", "best.pt")
    if not os.path.exists(best_pt):
        best_pt = os.path.join(service_dir, "runs", run_name, "weights", "last.pt")

    target_weights_path = os.path.join(service_dir, output_weights)
    os.makedirs(os.path.dirname(target_weights_path), exist_ok=True)

    if os.path.exists(best_pt):
        shutil.copy(best_pt, target_weights_path)
        print(f"\n HUẤN LUYỆN THÀNH CÔNG!")
        print(f" Mô hình đã được lưu vào: {target_weights_path}")
    else:
        print(f"\n Cảnh báo: Không tìm thấy file {best_pt}")

    # Chạy kiểm tra nhanh trên tập validation
    print("\n Đang đánh giá chất lượng mô hình...")
    trained_model = YOLO(target_weights_path)
    metrics = trained_model.val(data=data_yaml, imgsz=imgsz, device=device)
    print(f" -> mAP50: {metrics.box.map50:.4f}")
    print(f" -> mAP50-95: {metrics.box.map:.4f}")

    return target_weights_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Huấn luyện YOLOv8 nhận diện điện thoại iPhone")
    parser.add_argument("--epochs", type=int, default=15, help="Số epoch huấn luyện (mặc định: 15)")
    parser.add_argument("--batch", type=int, default=8, help="Batch size (mặc định: 8)")
    parser.add_argument("--imgsz", type=int, default=640, help="Kích thước ảnh đầu vào (mặc định: 640)")
    parser.add_argument("--data", type=str, default=None, help="Đường dẫn file data.yaml")
    parser.add_argument("--name", type=str, default="iphone_detect", help="Tên thư mục lưu lần train")
    parser.add_argument("--output", type=str, default="weights/yolo_phone_detect.pt", help="Đường dẫn file weights đầu ra")
    args = parser.parse_args()

    train_phone_detector(
        data_yaml=args.data,
        epochs=args.epochs,
        batch_size=args.batch,
        imgsz=args.imgsz,
        output_weights=args.output,
        run_name=args.name
    )
