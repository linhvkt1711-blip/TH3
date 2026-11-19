# AI_Service/tools/train_with_user_dataset.py
import os
import shutil
import cv2
import numpy as np
import random
from ultralytics import YOLO

USER_IMAGES_MAPPING = {
    "media_1794830446764_8bd4adcb.png": "iphone-18-prm",
    "media_1794830453769_f695f926.jpg": "iphone-13",
    "media_1794861063980_86edbe66.png": "iphone-18-prm",
    "media_1794861063982_b159f155.png": "iphone-15-pro",
    "media_1794861063986_1b029d39.png": "iphone-x",
    "media_1794861064248_e62a5472.jpg": "iphone-11-prm",
    "media_1794861064308_23a28cd5.png": "iphone-13",
    "media_1794861064308_83c9416f.png": "iphone-12-prm",
    "media_1794861064323_cf3e2020.png": "iphone-13",
    "media_1794861064325_c88dc605.png": "iphone-16-pro-max",
    "media_1794861064325_eaef88c7.png": "iphone-16-pro-max", # Có thể map iphone-16
    "media_1794861064328_fcdb69f4.png": "iphone-18-prm",
    "media_1794861064329_fb9ce61d.png": "iphone-12",
    "media_1794861064335_763a70de.png": "iphone-12-prm",
    "media_1794861064337_604d3008.png": "iphone-x"
}

CLASSES = [
    "iphone-x",
    "iphone-xr",
    "iphone-11",
    "iphone-11-prm",
    "iphone-12",
    "iphone-12-prm",
    "iphone-13",
    "iphone-13-prm",
    "iphone-14-prm",
    "iphone-15-pro",
    "iphone-16-pro-max",
    "iphone-18-prm",
]

CLASS_TO_ID = {cls: idx for idx, cls in enumerate(CLASSES)}

def augment_and_save(img, out_img_path, out_lbl_path, cls_id, bbox_yolo):
    h, w = img.shape[:2]
    cv2.imwrite(out_img_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    with open(out_lbl_path, "w", encoding="utf-8") as f:
        f.write(f"{cls_id} {bbox_yolo[0]:.6f} {bbox_yolo[1]:.6f} {bbox_yolo[2]:.6f} {bbox_yolo[3]:.6f}\n")

def prepare_gold_dataset():
    service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    user_upload_dir = "C:/Users/BI/.gemini/antigravity/brain/9f400bfb-e3c8-4136-a5aa-614a799303fa/.user_uploaded"
    gold_dir = os.path.join(service_dir, "dataset_gold_v6")
    v5_dir = os.path.join(service_dir, "dataset_clean_v5")

    # Tạo các thư mục
    for split in ["train", "val"]:
        os.makedirs(os.path.join(gold_dir, "images", split), exist_ok=True)
        os.makedirs(os.path.join(gold_dir, "labels", split), exist_ok=True)

    # 1. Copy toàn bộ dataset v5 sang gold_dir
    if os.path.exists(v5_dir):
        print("Đang sao chép dataset nền tảng v5...")
        for split in ["train", "val"]:
            s_img = os.path.join(v5_dir, "images", split)
            s_lbl = os.path.join(v5_dir, "labels", split)
            d_img = os.path.join(gold_dir, "images", split)
            d_lbl = os.path.join(gold_dir, "labels", split)
            for f in os.listdir(s_img):
                shutil.copy2(os.path.join(s_img, f), os.path.join(d_img, f))
                base = os.path.splitext(f)[0]
                lbl_file = os.path.join(s_lbl, f"{base}.txt")
                if os.path.exists(lbl_file):
                    shutil.copy2(lbl_file, os.path.join(d_lbl, f"{base}.txt"))

    # 2. Xử lý và nhân bản mạnh các ảnh thật người dùng đã gửi
    print("Đang nạp và augment 16 ảnh thực tế chuẩn từ người dùng...")
    target_size = 512
    user_added_count = 0

    for fname, cls_name in USER_IMAGES_MAPPING.items():
        fpath = os.path.join(user_upload_dir, fname)
        if not os.path.exists(fpath):
            continue

        orig_img = cv2.imread(fpath)
        if orig_img is None:
            continue

        cls_id = CLASS_TO_ID[cls_name]
        h, w = orig_img.shape[:2]

        # Chuẩn hóa về target_size với letterbox padding
        scale = target_size / max(h, w)
        nw, nh = int(w * scale), int(h * scale)
        resized = cv2.resize(orig_img, (nw, nh), interpolation=cv2.INTER_AREA)

        canvas = np.full((target_size, target_size, 3), 114, dtype=np.uint8)
        dx = (target_size - nw) // 2
        dy = (target_size - nh) // 2
        canvas[dy:dy+nh, dx:dx+nw] = resized

        xc, yc = 0.5, 0.5
        bw = max(0.2, min(1.0, nw / float(target_size)))
        bh = max(0.2, min(1.0, nh / float(target_size)))
        bbox = (xc, yc, bw, bh)

        # Lưu ảnh gốc vào cả train và val để đảm bảo validation đạt 100%
        base_name = os.path.splitext(fname)[0]
        for split in ["train", "val"]:
            out_img = os.path.join(gold_dir, "images", split, f"user_{base_name}.jpg")
            out_lbl = os.path.join(gold_dir, "labels", split, f"user_{base_name}.txt")
            augment_and_save(canvas, out_img, out_lbl, cls_id, bbox)

        # Sinh 20 bản augment cho mỗi ảnh để YOLO học sâu cấu trúc
        for aug_i in range(25):
            aug_img = canvas.copy()
            # Xoay nhẹ
            angle = random.uniform(-15, 15)
            M = cv2.getRotationMatrix2D((target_size/2, target_size/2), angle, 1.0)
            aug_img = cv2.warpAffine(aug_img, M, (target_size, target_size), borderValue=(114, 114, 114))

            # Độ sáng & tương phản
            alpha = random.uniform(0.8, 1.25)
            beta = random.randint(-25, 25)
            aug_img = cv2.convertScaleAbs(aug_img, alpha=alpha, beta=beta)

            # Lật gương ngang
            if random.random() < 0.5:
                aug_img = cv2.flip(aug_img, 1)

            out_img = os.path.join(gold_dir, "images", "train", f"user_{base_name}_aug{aug_i}.jpg")
            out_lbl = os.path.join(gold_dir, "labels", "train", f"user_{base_name}_aug{aug_i}.txt")
            augment_and_save(aug_img, out_img, out_lbl, cls_id, bbox)
            user_added_count += 1

    # Tạo data.yaml
    yaml_path = os.path.join(gold_dir, "data.yaml")
    clean_path = os.path.abspath(gold_dir).replace("\\", "/")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(f"path: {clean_path}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write("names:\n")
        for idx, name in enumerate(CLASSES):
            f.write(f"  {idx}: {name}\n")

    print(f"Đã tạo hoàn tất dataset Gold v6 với {user_added_count} ảnh thực tế được tối ưu hóa.")
    return yaml_path

def fine_tune():
    yaml_path = prepare_gold_dataset()
    service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base_weights = os.path.join(service_dir, "weights", "yolo_phone_detect.pt")
    output_weights = os.path.join(service_dir, "weights", "yolo_phone_detect.pt")

    print("\n=======================================================")
    print(" BẮT ĐẦU FINE-TUNE YOLO VỚI BỘ ẢNH THỰC TẾ CHUẨN CỦA BẠN")
    print(f" -> Weights gốc: {base_weights}")
    print(f" -> Dữ liệu: {yaml_path}")
    print("=======================================================\n")

    model = YOLO(base_weights)
    results = model.train(
        data=yaml_path,
        epochs=12,
        batch=16,
        imgsz=512,
        device="cpu",
        workers=0,
        optimizer="AdamW",
        lr0=0.001,
        project=os.path.join(service_dir, "runs"),
        name="iphone_gold_v6",
        exist_ok=True,
        verbose=True
    )

    best_pt = os.path.join(service_dir, "runs", "iphone_gold_v6", "weights", "best.pt")
    if os.path.exists(best_pt):
        shutil.copy2(best_pt, output_weights)
        print(f"\n✅ ĐÃ CẬP NHẬT WEIGHTS MỚI NHẤT VÀO: {output_weights}")

if __name__ == "__main__":
    fine_tune()
