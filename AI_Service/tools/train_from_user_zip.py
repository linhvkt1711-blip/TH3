# AI_Service/tools/train_from_user_zip.py
import os
import sys
import shutil
import random
import cv2
import numpy as np
from PIL import Image

# Đặt cấu hình Ultralytics cục bộ
current_dir = os.path.dirname(os.path.abspath(__file__))
service_dir = os.path.dirname(current_dir)
os.environ["YOLO_CONFIG_DIR"] = os.path.join(service_dir, ".config")

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
    "iphone-17-prm",
    "iphone-18-prm",
]

CLASS_TO_ID = {cls: idx for idx, cls in enumerate(CLASSES)}

FILE_TO_CLASS = {
    "Iphone X (2).jpg": "iphone-x",
    "iphone x.jpg": "iphone-x",
    "iphone XR.png": "iphone-xr",
    "iPhone 11.jpg": "iphone-11",
    "iPhone 11 Pro Max.jpg": "iphone-11-prm",
    "iPhone 12.jpg": "iphone-12",
    "iPhone 12 Pro Max.jpg": "iphone-12-prm",
    "iPhone 12 Pro Max (2).jpg": "iphone-12-prm",
    "iphone 13.jpg": "iphone-13",
    "iphone 13 (1).jpg": "iphone-13",
    "iPhone 13 (2).jpg": "iphone-13",
    "iphone 13 pro max.jpg": "iphone-13-prm",
    "iphone 14 pro max.png": "iphone-14-prm",
    "iphone 15 pro.jpg": "iphone-15-pro",
    "iPhone 15.jpg": "iphone-15-pro",
    "iPhone 16 Pro Max.jpg": "iphone-16-pro-max",
    "iPhone 16.jpg": "iphone-16-pro-max",
    "iphone 17 pro max.png": "iphone-17-prm",
    "iphone 18 pro max.png": "iphone-18-prm",
    "iphone 18 pro.png": "iphone-18-prm",
}

def generate_background(w, h):
    """Tạo hình nền thực tế mô phỏng bàn làm việc, ánh sáng tự nhiên."""
    bg_type = random.choice(["wood", "desk", "marble", "ambient", "gradient"])
    bg = np.zeros((h, w, 3), dtype=np.uint8)

    if bg_type == "wood":
        base_color = np.array([random.randint(25, 60), random.randint(50, 95), random.randint(90, 150)], dtype=np.float32)
        bg[:] = base_color
        noise = np.random.normal(0, 8, (h, w, 3))
        bg = np.clip(bg + noise, 0, 255).astype(np.uint8)
    elif bg_type == "marble":
        val = random.randint(200, 240)
        bg[:] = [val, val, val]
        noise = np.random.normal(0, 10, (h, w, 3))
        bg = np.clip(bg + noise, 0, 255).astype(np.uint8)
    elif bg_type == "desk":
        val = random.randint(35, 75)
        bg[:] = [val, val, val]
    elif bg_type == "gradient":
        c1 = [random.randint(30, 110) for _ in range(3)]
        c2 = [random.randint(40, 140) for _ in range(3)]
        for y in range(h):
            alpha = y / float(h)
            bg[y, :] = [int(c1[i] * (1 - alpha) + c2[i] * alpha) for i in range(3)]
    else:
        val = random.randint(80, 160)
        bg[:] = [val, val, val]

    return bg

def composite_phone_on_background(phone_img, bg_size=512, scale_range=(0.60, 0.90), rotate_range=(-12, 12)):
    """Đặt ảnh điện thoại lên nền và tính toán Bounding Box YOLO."""
    h_bg, w_bg = bg_size, bg_size
    bg = generate_background(w_bg, h_bg)

    # Đọc kênh alpha nếu có
    has_alpha = phone_img.shape[2] == 4
    if has_alpha:
        bgr = phone_img[:, :, :3]
        alpha = phone_img[:, :, 3]
    else:
        bgr = phone_img
        # Nếu là nền trắng, tạo mask tự động
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        _, alpha = cv2.threshold(gray, 248, 255, cv2.THRESH_BINARY_INV)
        # Khử viền răng cưa
        alpha = cv2.GaussianBlur(alpha, (3, 3), 0)

    ph, pw = bgr.shape[:2]
    target_scale = random.uniform(*scale_range)
    scale = (bg_size * target_scale) / float(max(ph, pw))
    new_w = max(20, int(pw * scale))
    new_h = max(40, int(ph * scale))

    resized_bgr = cv2.resize(bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
    resized_alpha = cv2.resize(alpha, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Xoay nhẹ
    angle = random.uniform(*rotate_range)
    if abs(angle) > 1.0:
        rot_mat = cv2.getRotationMatrix2D((new_w / 2.0, new_h / 2.0), angle, 1.0)
        resized_bgr = cv2.warpAffine(resized_bgr, rot_mat, (new_w, new_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        resized_alpha = cv2.warpAffine(resized_alpha, rot_mat, (new_w, new_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    # Thay đổi độ sáng/tương phản
    alpha_factor = random.uniform(0.85, 1.15)
    beta_factor = random.randint(-15, 15)
    resized_bgr = np.clip(resized_bgr * alpha_factor + beta_factor, 0, 255).astype(np.uint8)

    # Lật ngang ngẫu nhiên (50% webcam lật)
    if random.random() < 0.35:
        resized_bgr = cv2.flip(resized_bgr, 1)
        resized_alpha = cv2.flip(resized_alpha, 1)

    # Vị trí đặt trên background
    max_x = max(0, w_bg - new_w)
    max_y = max(0, h_bg - new_h)
    pos_x = random.randint(0, max_x)
    pos_y = random.randint(0, max_y)

    mask = resized_alpha.astype(float) / 255.0
    mask_3d = np.dstack([mask, mask, mask])

    roi = bg[pos_y:pos_y + new_h, pos_x:pos_x + new_w]
    blended = (resized_bgr * mask_3d + roi * (1.0 - mask_3d)).astype(np.uint8)
    bg[pos_y:pos_y + new_h, pos_x:pos_x + new_w] = blended

    # Tính Bounding Box chuẩn YOLO (x_center, y_center, width, height theo tỉ lệ 0..1)
    bx1 = pos_x
    by1 = pos_y
    bx2 = pos_x + new_w
    by2 = pos_y + new_h

    # Thu hẹp bounding box bám sát phần alpha thực tế
    non_zero = np.where(resized_alpha > 30)
    if len(non_zero[0]) > 0 and len(non_zero[1]) > 0:
        min_y, max_y_a = np.min(non_zero[0]), np.max(non_zero[0])
        min_x, max_x_a = np.min(non_zero[1]), np.max(non_zero[1])
        bx1 = pos_x + min_x
        by1 = pos_y + min_y
        bx2 = pos_x + max_x_a
        by2 = pos_y + max_y_a

    bw = max(1, bx2 - bx1)
    bh = max(1, by2 - by1)
    cx = (bx1 + bx2) / 2.0 / w_bg
    cy = (by1 + by2) / 2.0 / h_bg
    nw = bw / float(w_bg)
    nh = bh / float(h_bg)

    # Bounded to [0, 1]
    cx = max(0.01, min(0.99, cx))
    cy = max(0.01, min(0.99, cy))
    nw = max(0.02, min(0.99, nw))
    nh = max(0.02, min(0.99, nh))

    return bg, (cx, cy, nw, nh)

def build_dataset_and_train(epochs=20):
    raw_images_dir = os.path.join(service_dir, "user_uploaded_extracted")
    if not os.path.exists(raw_images_dir):
        print(f"Lỗi: Không tìm thấy thư mục {raw_images_dir}")
        return

    output_dataset = os.path.join(service_dir, "dataset_user_augmented")
    for split in ["train", "val"]:
        os.makedirs(os.path.join(output_dataset, "images", split), exist_ok=True)
        os.makedirs(os.path.join(output_dataset, "labels", split), exist_ok=True)

    print("=================================================================")
    print(" 1. TẠO TẬP DỮ LIỆU AUGMENT TỪ ẢNH MẶT SAU THỰC TẾ NGƯỜI DÙNG")
    print(f" -> Nguồn ảnh: {raw_images_dir}")
    print(f" -> Đích dataset: {output_dataset}")
    print("=================================================================")

    # Đọc tất cả ảnh trong thư mục
    files = [f for f in os.listdir(raw_images_dir) if os.path.isfile(os.path.join(raw_images_dir, f))]
    total_samples = 0

    samples_per_image = 15 # Mỗi ảnh thật tạo ra 15 biến thể góc/ánh sáng/nền

    for f in files:
        cls_name = FILE_TO_CLASS.get(f)
        if not cls_name or cls_name not in CLASS_TO_ID:
            print(f"Bỏ qua file không xác định: {f}")
            continue

        cls_id = CLASS_TO_ID[cls_name]
        img_path = os.path.join(raw_images_dir, f)
        phone_img = cv2.imread(img_path, cv2.IMREAD_UNCHANGED)
        if phone_img is None:
            continue

        base_name = os.path.splitext(f)[0].replace(" ", "_").replace("(", "").replace(")", "").lower()

        for idx in range(samples_per_image):
            # 80% train, 20% val
            split = "val" if (idx % 5 == 0) else "train"

            # Tỉ lệ zoom và góc xoay
            scale_range = (0.65, 0.95) if split == "train" else (0.70, 0.90)
            rotate_range = (-15, 15) if split == "train" else (-5, 5)

            comp_img, (cx, cy, nw, nh) = composite_phone_on_background(
                phone_img, bg_size=512, scale_range=scale_range, rotate_range=rotate_range
            )

            sample_name = f"{cls_name}_{base_name}_{idx:03d}"
            out_img = os.path.join(output_dataset, "images", split, f"{sample_name}.jpg")
            out_lbl = os.path.join(output_dataset, "labels", split, f"{sample_name}.txt")

            cv2.imwrite(out_img, comp_img, [cv2.IMWRITE_JPEG_QUALITY, 92])
            with open(out_lbl, "w", encoding="utf-8") as lf:
                lf.write(f"{cls_id} {cx:.6f} {cy:.6f} {nw:.6f} {nh:.6f}\n")

            total_samples += 1

    print(f"✅ Đã tạo thành công {total_samples} ảnh mẫu gán nhãn cho {len(CLASSES)} dòng iPhone!")

    # Tạo data.yaml
    yaml_content = f"""path: {output_dataset.replace(chr(92), '/')}
train: images/train
val: images/val
names:
"""
    for idx, c in enumerate(CLASSES):
        yaml_content += f"  {idx}: {c}\n"

    data_yaml_path = os.path.join(output_dataset, "data.yaml")
    with open(data_yaml_path, "w", encoding="utf-8") as yf:
        yf.write(yaml_content)

    print(f"✅ Đã lưu cấu hình: {data_yaml_path}")

    # Tiến hành Train YOLOv8
    print("\n=================================================================")
    print(" 2. TIẾN HÀNH HUẤN LUYỆN YOLOv8 VỚI WEIGHTS GỐC")
    print(f" -> Số Epochs: {epochs}")
    print(f" -> Data: {data_yaml_path}")
    print("=================================================================")

    from ultralytics import YOLO

    base_model = os.path.join(service_dir, "weights", "yolov8n.pt")
    if not os.path.exists(base_model):
        base_model = "yolov8n.pt"

    model = YOLO(base_model)
    run_name = "iphone_user_augmented"

    results = model.train(
        data=data_yaml_path,
        epochs=epochs,
        batch=16,
        imgsz=320,
        device="cpu",
        workers=0,
        optimizer="AdamW",
        lr0=0.002,
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

    target_weights = os.path.join(service_dir, "weights", "yolo_phone_detect.pt")
    if os.path.exists(best_pt):
        shutil.copy2(best_pt, target_weights)
        print(f"\n🎉 HUẤN LUYỆN THÀNH CÔNG RỰC RỠ!")
        print(f"👉 File weights đã được lưu tại: {target_weights}")
    else:
        print(f"\n⚠️ Cảnh báo: Không tìm thấy file {best_pt}")

if __name__ == "__main__":
    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 15
    build_dataset_and_train(epochs=epochs)
