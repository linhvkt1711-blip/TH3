# AI_Service/train_master.py
import os
import shutil
from ultralytics import YOLO

def train():
    service_dir = os.path.dirname(os.path.abspath(__file__))
    data_yaml = os.path.join(service_dir, "dataset_master_v7", "data.yaml")
    base_model = os.path.join(service_dir, "weights", "yolo_phone_detect.pt")
    if not os.path.exists(base_model):
        base_model = os.path.join(service_dir, "weights", "yolov8n.pt")
        if not os.path.exists(base_model):
            base_model = "yolov8n.pt"

    output_weights = os.path.join(service_dir, "weights", "yolo_phone_detect.pt")
    run_name = "iphone_master_v7"

    print("=================================================================")
    print(" BẮT ĐẦU HUẤN LUYỆN CHUYÊN SÂU YOLOv8 - IPHONE REAR RECOGNITION")
    print(f" -> Dữ liệu: {data_yaml}")
    print(f" -> Base Model: {base_model}")
    print(f" -> Output weights: {output_weights}")
    print("=================================================================\n")

    model = YOLO(base_model)

    results = model.train(
        data=data_yaml,
        epochs=15,
        batch=16,
        imgsz=512,
        device="cpu",
        workers=0,
        optimizer="AdamW",
        lr0=0.0015,
        cos_lr=True,
        augment=True,
        fliplr=0.5,
        project=os.path.join(service_dir, "runs"),
        name=run_name,
        exist_ok=True,
        verbose=True
    )

    best_pt = os.path.join(service_dir, "runs", run_name, "weights", "best.pt")
    if not os.path.exists(best_pt):
        best_pt = os.path.join(service_dir, "runs", run_name, "weights", "last.pt")

    if os.path.exists(best_pt):
        os.makedirs(os.path.dirname(output_weights), exist_ok=True)
        shutil.copy2(best_pt, output_weights)
        print(f"\n✅ ĐÃ HUẤN LUYỆN THÀNH CÔNG VÀ LƯU WEIGHTS: {output_weights}")
    else:
        print("\n⚠️ Không tìm thấy weights kết quả.")

if __name__ == "__main__":
    train()
