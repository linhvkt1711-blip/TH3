# AI_Service/tools/fetch_real_and_build_dataset.py
import os
import sys
import shutil
import random
import cv2
import numpy as np
from icrawler.builtin import BaiduImageCrawler

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
    "iphone-18",
    "iphone-18-prm",
    "samsung-s24-ultra",
    "iphone-15-prm"
]

CLASS_TO_ID = {cls: idx for idx, cls in enumerate(CLASSES)}

CRAWL_KEYWORDS = {
    "iphone-x": ["iPhone X 后盖", "iPhone X back camera"],
    "iphone-xr": ["iPhone XR 后盖", "iPhone XR back view"],
    "iphone-11": ["iPhone 11 后盖", "iPhone 11 dual camera back"],
    "iphone-11-prm": ["iPhone 11 Pro Max 后盖", "iPhone 11 Pro Max back camera"],
    "iphone-12": ["iPhone 12 后盖", "iPhone 12 back camera"],
    "iphone-12-prm": ["iPhone 12 Pro Max 后盖", "iPhone 12 Pro Max back view"],
    "iphone-13": ["iPhone 13 后盖", "iPhone 13 back camera diagonal"],
    "iphone-13-prm": ["iPhone 13 Pro Max 后盖", "iPhone 13 Pro Max camera back"],
    "iphone-14-prm": ["iPhone 14 Pro Max 后盖", "iPhone 14 Pro Max back"],
    "iphone-15-pro": ["iPhone 15 Pro 后盖", "iPhone 15 Pro natural titanium back"],
    "iphone-15-prm": ["iPhone 15 Pro Max 后盖", "iPhone 15 Pro Max titanium back"],
    "iphone-16-pro-max": ["iPhone 16 Pro Max 后盖", "iPhone 16 Pro Max desert titanium back"],
    "samsung-s24-ultra": ["Galaxy S24 Ultra 后盖", "Samsung S24 Ultra back view"]
}

def crawl_real_images(raw_dir, max_per_query=12):
    os.makedirs(raw_dir, exist_ok=True)
    print("=== BẮT ĐẦU THU THẬP ẢNH MẶT SAU THỰC TẾ ===")
    for cls_name, queries in CRAWL_KEYWORDS.items():
        cls_dir = os.path.join(raw_dir, cls_name)
        os.makedirs(cls_dir, exist_ok=True)
        existing = len([f for f in os.listdir(cls_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg'))])
        if existing >= 15:
            print(f"[{cls_name}] Đã có {existing} ảnh, bỏ qua crawl.")
            continue
        print(f"Đang crawl ảnh cho [{cls_name}]...")
        for q in queries:
            try:
                crawler = BaiduImageCrawler(
                    storage={'root_dir': cls_dir},
                    log_level=30
                )
                crawler.crawl(keyword=q, max_num=max_per_query)
            except Exception as e:
                print(f"Lỗi crawl {q}: {e}")

def process_and_merge_dataset(raw_dir, synthetic_v4_dir, output_dir, target_size=640):
    images_train = os.path.join(output_dir, "images", "train")
    images_val = os.path.join(output_dir, "images", "val")
    labels_train = os.path.join(output_dir, "labels", "train")
    labels_val = os.path.join(output_dir, "labels", "val")

    for d in [images_train, images_val, labels_train, labels_val]:
        os.makedirs(d, exist_ok=True)

    print("=== NẠP VÀ GỘP DATASET SYNTHETIC HIỆN CÓ ===")
    if os.path.isdir(synthetic_v4_dir):
        for split in ["train", "val"]:
            s_img = os.path.join(synthetic_v4_dir, "images", split)
            s_lbl = os.path.join(synthetic_v4_dir, "labels", split)
            d_img = images_val if split == "val" else images_train
            d_lbl = labels_val if split == "val" else labels_train
            if os.path.isdir(s_img):
                for f in os.listdir(s_img):
                    if f.lower().endswith(('.jpg', '.png', '.jpeg')):
                        base = os.path.splitext(f)[0]
                        shutil.copy2(os.path.join(s_img, f), os.path.join(d_img, f))
                        lbl_file = os.path.join(s_lbl, f"{base}.txt")
                        if os.path.exists(lbl_file):
                            shutil.copy2(lbl_file, os.path.join(d_lbl, f"{base}.txt"))

    print("=== XỬ LÝ VÀ CHUẨN HÓA ẢNH THỰC TẾ ===")
    real_count = 0
    if os.path.isdir(raw_dir):
        for cls_name in os.listdir(raw_dir):
            cls_path = os.path.join(raw_dir, cls_name)
            if not os.path.isdir(cls_path) or cls_name not in CLASS_TO_ID:
                continue
            cls_id = CLASS_TO_ID[cls_name]
            files = [f for f in os.listdir(cls_path) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.webp'))]
            print(f"Xử lý {len(files)} ảnh thật cho {cls_name}...")
            for idx, fname in enumerate(files):
                img_path = os.path.join(cls_path, fname)
                img = cv2.imread(img_path)
                if img is None:
                    continue
                h, w = img.shape[:2]
                if h < 100 or w < 100:
                    continue

                # Chuẩn hóa về target_size với letterbox padding
                scale = target_size / max(h, w)
                nw, nh = int(w * scale), int(h * scale)
                resized = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA)

                canvas = np.full((target_size, target_size, 3), 114, dtype=np.uint8)
                dx = (target_size - nw) // 2
                dy = (target_size - nh) // 2
                canvas[dy:dy+nh, dx:dx+nw] = resized

                # Bounding box chuẩn hóa
                xc = 0.5
                yc = 0.5
                box_w = max(0.1, min(1.0, nw / float(target_size)))
                box_h = max(0.1, min(1.0, nh / float(target_size)))

                is_val = (idx % 5 == 0) # 20% val
                target_img_dir = images_val if is_val else images_train
                target_lbl_dir = labels_val if is_val else labels_train

                out_base = f"real_{cls_name}_{idx:04d}"
                out_img_path = os.path.join(target_img_dir, f"{out_base}.jpg")
                out_lbl_path = os.path.join(target_lbl_dir, f"{out_base}.txt")

                cv2.imwrite(out_img_path, canvas, [cv2.IMWRITE_JPEG_QUALITY, 95])
                with open(out_lbl_path, "w", encoding="utf-8") as lf:
                    lf.write(f"{cls_id} {xc:.6f} {yc:.6f} {box_w:.6f} {box_h:.6f}\n")
                real_count += 1

                # Tạo thêm 1 bản flip ngang để học cả 2 hướng camera
                if not is_val:
                    flipped = cv2.flip(canvas, 1)
                    flip_base = f"real_{cls_name}_{idx:04d}_flip"
                    cv2.imwrite(os.path.join(images_train, f"{flip_base}.jpg"), flipped, [cv2.IMWRITE_JPEG_QUALITY, 95])
                    with open(os.path.join(labels_train, f"{flip_base}.txt"), "w", encoding="utf-8") as lf:
                        lf.write(f"{cls_id} {xc:.6f} {yc:.6f} {box_w:.6f} {box_h:.6f}\n")
                    real_count += 1

    # Tạo data.yaml
    yaml_path = os.path.join(output_dir, "data.yaml")
    clean_path = os.path.abspath(output_dir).replace("\\", "/")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(f"path: {clean_path}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write("names:\n")
        for idx, name in enumerate(CLASSES):
            f.write(f"  {idx}: {name}\n")

    train_c = len(os.listdir(images_train))
    val_c = len(os.listdir(images_val))
    print(f"\n=== HOÀN TẤT TẠO DATASET V5 (SYNTHETIC + REAL) ===")
    print(f"Tổng Train: {train_c} ảnh | Val: {val_c} ảnh")
    print(f"Đã thêm {real_count} ảnh thật (gốc + augmented).")
    print(f"File data.yaml: {yaml_path}")
    return yaml_path

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(base_dir, "dataset_real_raw")
    v4_dir = os.path.join(base_dir, "dataset_clean_v4")
    v5_dir = os.path.join(base_dir, "dataset_clean_v5")

    crawl_real_images(raw_dir, max_per_query=15)
    process_and_merge_dataset(raw_dir, v4_dir, v5_dir, target_size=640)
