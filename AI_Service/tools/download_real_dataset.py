# AI_Service/tools/download_real_dataset.py
"""
Script tải ảnh thật mặt sau (back) các dòng iPhone từ internet,
xử lý, augment và tổ chức thành dataset chuẩn YOLO để train
nhận diện chính xác từng dòng iPhone khi quét camera hoặc upload ảnh.

Cách dùng:
    python tools/download_real_dataset.py                     # Tải + build dataset
    python tools/download_real_dataset.py --skip-download      # Chỉ build từ ảnh đã tải
    python tools/download_real_dataset.py --max-images 80      # Tải 80 ảnh mỗi class
    python tools/download_real_dataset.py --output dataset_real_v1  # Thư mục output khác

Yêu cầu:
    pip install requests Pillow opencv-python tqdm
"""

import os
import sys
import re
import json
import time
import random
import hashlib
import argparse
import shutil
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
    import cv2
    import numpy as np
    from tqdm import tqdm
    HAS_DEPS = True
except ImportError as e:
    HAS_DEPS = False
    print(f"[!] Thiếu thư viện: {e}")
    print("    Chạy: pip install requests Pillow opencv-python numpy tqdm")

# ============================================================================
# CẤU HÌNH CÁC DÒNG IPHONE VÀ TỪ KHOÁ TÌM KIẾM
# ============================================================================

PHONE_SEARCH_QUERIES = {
    "iphone-x": [
        "iPhone X back view",
        "iPhone X rear camera",
        "iPhone X space gray back",
        "iPhone Xs back silver",
        "iPhone X mặt sau",
        "iPhone X rear panel",
        "iPhone X back glass",
        "iPhone X vertical dual camera back",
    ],
    "iphone-xr": [
        "iPhone XR back view",
        "iPhone XR single camera back",
        "iPhone XR rear panel",
        "iPhone XR back color",
        "iPhone XR mặt sau",
        "iPhone XR back case off",
        "iPhone XR rear camera module",
    ],
    "iphone-11": [
        "iPhone 11 back view",
        "iPhone 11 dual camera square",
        "iPhone 11 rear panel",
        "iPhone 11 back purple green",
        "iPhone 11 mặt sau",
        "iPhone 11 camera module back",
        "iPhone 11 back design",
    ],
    "iphone-11-prm": [
        "iPhone 11 Pro Max back view",
        "iPhone 11 Pro Max triple camera",
        "iPhone 11 Pro Max rear",
        "iPhone 11 Pro back midnight green",
        "iPhone 11 Pro Max mặt sau",
        "iPhone 11 Pro Max camera module",
        "iPhone 11 Pro Max frosted glass back",
    ],
    "iphone-12": [
        "iPhone 12 back view",
        "iPhone 12 dual camera back flat edge",
        "iPhone 12 rear panel",
        "iPhone 12 back blue purple",
        "iPhone 12 mặt sau",
        "iPhone 12 back design flat",
        "iPhone 12 rear camera diagonal",
    ],
    "iphone-12-prm": [
        "iPhone 12 Pro Max back view",
        "iPhone 12 Pro Max triple camera",
        "iPhone 12 Pro Max rear LiDAR",
        "iPhone 12 Pro Max pacific blue back",
        "iPhone 12 Pro Max mặt sau",
        "iPhone 12 Pro Max camera module",
    ],
    "iphone-13": [
        "iPhone 13 back view",
        "iPhone 13 diagonal camera back",
        "iPhone 13 rear panel",
        "iPhone 13 pink blue back",
        "iPhone 13 mặt sau",
        "iPhone 13 back camera diagonal layout",
    ],
    "iphone-13-prm": [
        "iPhone 13 Pro Max back view",
        "iPhone 13 Pro Max triple camera",
        "iPhone 13 Pro Max sierra blue back",
        "iPhone 13 Pro Max rear alpine green",
        "iPhone 13 Pro Max mặt sau",
        "iPhone 13 Pro Max camera module large",
    ],
    "iphone-14-prm": [
        "iPhone 14 Pro Max back view",
        "iPhone 14 Pro Max triple camera",
        "iPhone 14 Pro Max deep purple back",
        "iPhone 14 Pro Max rear space black",
        "iPhone 14 Pro Max mặt sau",
        "iPhone 14 Pro Max camera module big",
    ],
    "iphone-15-pro": [
        "iPhone 15 Pro back view",
        "iPhone 15 Pro triple camera titanium",
        "iPhone 15 Pro natural titanium back",
        "iPhone 15 Pro rear blue titanium",
        "iPhone 15 Pro mặt sau",
        "iPhone 15 Pro action button back",
    ],
    "iphone-16-pro-max": [
        "iPhone 16 Pro Max back view",
        "iPhone 16 Pro Max camera control button",
        "iPhone 16 Pro Max desert titanium back",
        "iPhone 16 Pro Max rear panel",
        "iPhone 16 Pro Max mặt sau",
        "iPhone 16 Pro Max triple camera large back",
    ],
    "iphone-18-prm": [
        "iPhone 18 Pro Max back view",
        "iPhone 18 Pro Max camera module",
        "iPhone 18 Pro Max rear panel",
        "iPhone 18 Pro Max mặt sau",
        "iPhone 18 Pro Max triple camera back",
    ],
}

CLASSES = list(PHONE_SEARCH_QUERIES.keys())
CLASS_TO_ID = {cls: idx for idx, cls in enumerate(CLASSES)}

# ============================================================================
# HÀM TẢI ẢNH TỪ BING IMAGE SEARCH (KHÔNG CẦN API KEY)
# ============================================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def search_bing_images(query, max_results=30):
    """
    Tìm kiếm ảnh trên Bing Images và trích xuất URL ảnh.
    Không cần API key - sử dụng web scraping cơ bản.
    """
    urls = []
    encoded_query = quote_plus(query)

    for offset in range(0, max_results, 35):
        search_url = (
            f"https://www.bing.com/images/search?q={encoded_query}"
            f"&first={offset}&count=35&qft=+filterui:imagesize-large"
            f"&form=IRFLTR"
        )
        try:
            resp = requests.get(search_url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            html = resp.text

            # Trích xuất URL ảnh từ HTML
            # Bing chứa URL ảnh trong thuộc tính murl
            murl_pattern = r'"murl":"(https?://[^"]+)"'
            found = re.findall(murl_pattern, html)
            urls.extend(found)

            # Backup: tìm trong src của thẻ img
            if not found:
                src_pattern = r'src="(https?://[^"]+(?:\.jpg|\.jpeg|\.png|\.webp)[^"]*)"'
                found2 = re.findall(src_pattern, html, re.IGNORECASE)
                urls.extend(found2)

            if len(urls) >= max_results:
                break
            time.sleep(random.uniform(0.5, 1.5))
        except Exception as e:
            print(f"  [Bing search error] {e}")
            continue

    # Loại bỏ trùng lặp, giữ thứ tự
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen and not any(skip in url.lower() for skip in [
            "bing.com", "microsoft.com", "favicon", "logo", "icon", "pixel",
            "tracking", "analytics", "badge", "button", ".svg", ".gif"
        ]):
            seen.add(url)
            unique_urls.append(url)
    return unique_urls[:max_results]


def search_duckduckgo_images(query, max_results=30):
    """
    Backup: tìm ảnh qua DuckDuckGo Images.
    """
    urls = []
    try:
        # DuckDuckGo cần token trước
        token_url = f"https://duckduckgo.com/?q={quote_plus(query)}&iax=images&ia=images"
        resp = requests.get(token_url, headers=HEADERS, timeout=10)
        vqd_match = re.search(r'vqd="([^"]+)"', resp.text)
        if not vqd_match:
            vqd_match = re.search(r"vqd='([^']+)'", resp.text)
        if not vqd_match:
            vqd_match = re.search(r'vqd=([^&"]+)', resp.text)

        if vqd_match:
            vqd = vqd_match.group(1)
            api_url = (
                f"https://duckduckgo.com/i.js?l=us-en&o=json&q={quote_plus(query)}"
                f"&vqd={vqd}&f=size:Large&p=1"
            )
            resp2 = requests.get(api_url, headers=HEADERS, timeout=10)
            data = resp2.json()
            for result in data.get("results", []):
                img_url = result.get("image", "")
                if img_url and img_url.startswith("http"):
                    urls.append(img_url)
    except Exception as e:
        print(f"  [DDG search error] {e}")

    return urls[:max_results]


def download_image(url, save_path, timeout=12):
    """Tải 1 ảnh từ URL, kiểm tra và lưu. Trả về True nếu thành công."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, stream=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "image" not in content_type and not url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            return False

        # Kiểm tra kích thước (bỏ qua ảnh quá nhỏ < 10KB hoặc quá lớn > 20MB)
        content_length = int(resp.headers.get("Content-Length", 0))
        if 0 < content_length < 10_000:
            return False

        img_data = resp.content
        if len(img_data) < 10_000:
            return False

        # Kiểm tra ảnh hợp lệ bằng PIL
        from io import BytesIO
        img = Image.open(BytesIO(img_data))
        img.verify()

        # Reload sau verify
        img = Image.open(BytesIO(img_data))
        w, h = img.size
        if w < 150 or h < 150:
            return False

        # Convert sang RGB và lưu
        if img.mode != "RGB":
            img = img.convert("RGB")

        img.save(save_path, "JPEG", quality=95)
        return True
    except Exception:
        return False


def download_dataset_for_class(class_name, queries, raw_dir, max_images=50):
    """Tải ảnh thật cho 1 class (dòng điện thoại)."""
    class_dir = os.path.join(raw_dir, class_name)
    os.makedirs(class_dir, exist_ok=True)

    # Đếm ảnh đã có
    existing = [f for f in os.listdir(class_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    if len(existing) >= max_images:
        print(f"  ✓ [{class_name}] Đã có {len(existing)} ảnh, bỏ qua tải thêm.")
        return len(existing)

    remaining = max_images - len(existing)
    all_urls = []

    print(f"  🔍 [{class_name}] Đang tìm kiếm ảnh trên internet...")
    for query in queries:
        urls = search_bing_images(query, max_results=max_images // len(queries) + 5)
        if len(urls) < 5:
            urls.extend(search_duckduckgo_images(query, max_results=10))
        all_urls.extend(urls)
        if len(all_urls) >= remaining * 2:
            break

    # Loại trùng lặp
    seen_hashes = set()
    unique_urls = []
    for url in all_urls:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:10]
        if url_hash not in seen_hashes:
            seen_hashes.add(url_hash)
            unique_urls.append(url)

    random.shuffle(unique_urls)
    downloaded = len(existing)

    print(f"  📥 [{class_name}] Tìm thấy {len(unique_urls)} URL, đang tải...")

    for i, url in enumerate(unique_urls):
        if downloaded >= max_images:
            break
        save_path = os.path.join(class_dir, f"real_{class_name}_{downloaded:04d}.jpg")
        if download_image(url, save_path):
            downloaded += 1
        if (i + 1) % 10 == 0:
            print(f"    [{class_name}] Đã tải {downloaded}/{max_images}...")

    print(f"  ✅ [{class_name}] Tổng cộng: {downloaded} ảnh")
    return downloaded


# ============================================================================
# XỬ LÝ ẢNH VÀ TẠO DATASET YOLO
# ============================================================================

def augment_image(img_cv, seed=None):
    """
    Augment ảnh với các biến đổi thực tế:
    - Xoay nhẹ (-20° đến +20°)
    - Lật ngang (50% xác suất)
    - Thay đổi độ sáng, contrast, saturation
    - Thêm noise nhẹ
    - Crop nhẹ và resize
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    h, w = img_cv.shape[:2]
    result = img_cv.copy()

    # 1. Xoay nhẹ
    if random.random() < 0.6:
        angle = random.uniform(-20, 20)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        result = cv2.warpAffine(result, M, (w, h), borderMode=cv2.BORDER_REFLECT)

    # 2. Lật ngang
    if random.random() < 0.5:
        result = cv2.flip(result, 1)

    # 3. Thay đổi brightness & contrast
    if random.random() < 0.7:
        alpha = random.uniform(0.7, 1.4)  # contrast
        beta = random.randint(-30, 30)  # brightness
        result = cv2.convertScaleAbs(result, alpha=alpha, beta=beta)

    # 4. Thay đổi saturation
    if random.random() < 0.4:
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] *= random.uniform(0.6, 1.5)
        hsv = np.clip(hsv, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # 5. Gaussian noise nhẹ
    if random.random() < 0.3:
        noise = np.random.normal(0, random.uniform(3, 12), result.shape).astype(np.float32)
        result = np.clip(result.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    # 6. Gaussian blur nhẹ
    if random.random() < 0.25:
        ksize = random.choice([3, 5])
        result = cv2.GaussianBlur(result, (ksize, ksize), 0)

    return result


def process_real_image(img_path, target_size=640):
    """
    Xử lý 1 ảnh thật: resize, letterbox padding.
    Trả về (image_cv, bbox_yolo) với bbox bao quanh vùng ảnh thật.
    """
    img = cv2.imread(img_path)
    if img is None:
        return None, None

    h, w = img.shape[:2]
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h * scale)
    resized = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # Letterbox padding
    canvas = np.full((target_size, target_size, 3), 114, dtype=np.uint8)  # gray padding
    dx = (target_size - new_w) // 2
    dy = (target_size - new_h) // 2
    canvas[dy:dy + new_h, dx:dx + new_w] = resized

    # Bounding box YOLO format (center_x, center_y, width, height) normalized
    # Bao quanh vùng ảnh thật (loại bỏ padding)
    margin = 0.03  # thêm margin nhỏ
    xc = 0.5
    yc = 0.5
    box_w = min(1.0, (new_w / target_size) + margin)
    box_h = min(1.0, (new_h / target_size) + margin)

    return canvas, (xc, yc, box_w, box_h)


def build_real_dataset(raw_dir, output_dir, augment_per_image=3, target_size=640, val_ratio=0.2):
    """
    Xây dựng dataset YOLO từ ảnh thật đã tải.

    Args:
        raw_dir: Thư mục chứa ảnh thô (mỗi class 1 thư mục con)
        output_dir: Thư mục output chuẩn YOLO
        augment_per_image: Số bản augment cho mỗi ảnh gốc
        target_size: Kích thước ảnh đầu ra
        val_ratio: Tỷ lệ validation
    """
    images_train = os.path.join(output_dir, "images", "train")
    images_val = os.path.join(output_dir, "images", "val")
    labels_train = os.path.join(output_dir, "labels", "train")
    labels_val = os.path.join(output_dir, "labels", "val")

    for d in [images_train, images_val, labels_train, labels_val]:
        os.makedirs(d, exist_ok=True)

    total_images = 0
    stats = {}

    print(f"\n{'='*60}")
    print(f" XÂY DỰNG DATASET YOLO TỪ ẢNH THẬT")
    print(f" Augment: {augment_per_image}x | Image size: {target_size}")
    print(f"{'='*60}\n")

    for cls_name in CLASSES:
        cls_id = CLASS_TO_ID[cls_name]
        cls_raw = os.path.join(raw_dir, cls_name)

        if not os.path.isdir(cls_raw):
            print(f"  ⚠ [{cls_name}] Không tìm thấy thư mục ảnh thô, bỏ qua.")
            stats[cls_name] = 0
            continue

        image_files = sorted([
            f for f in os.listdir(cls_raw)
            if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))
        ])

        if not image_files:
            print(f"  ⚠ [{cls_name}] Thư mục trống, bỏ qua.")
            stats[cls_name] = 0
            continue

        cls_count = 0
        val_count = max(1, int(len(image_files) * val_ratio))
        val_indices = set(random.sample(range(len(image_files)), min(val_count, len(image_files))))

        print(f"  📂 [{cls_name}] Xử lý {len(image_files)} ảnh gốc...")

        for idx, fname in enumerate(image_files):
            fpath = os.path.join(cls_raw, fname)
            processed, bbox = process_real_image(fpath, target_size)
            if processed is None or bbox is None:
                continue

            is_val = idx in val_indices
            xc, yc, bw, bh = bbox

            # Lưu ảnh gốc đã xử lý
            out_prefix = f"real_{cls_name}_{idx:04d}"
            if is_val:
                img_dir, lbl_dir = images_val, labels_val
            else:
                img_dir, lbl_dir = images_train, labels_train

            cv2.imwrite(
                os.path.join(img_dir, f"{out_prefix}_orig.jpg"),
                processed,
                [int(cv2.IMWRITE_JPEG_QUALITY), 95]
            )
            with open(os.path.join(lbl_dir, f"{out_prefix}_orig.txt"), "w") as f:
                f.write(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
            cls_count += 1

            # Tạo augmented versions
            for aug_i in range(augment_per_image):
                aug_img = augment_image(processed, seed=idx * 100 + aug_i)
                aug_name = f"{out_prefix}_aug{aug_i}"

                # Augmented images luôn vào train (không vào val)
                cv2.imwrite(
                    os.path.join(images_train, f"{aug_name}.jpg"),
                    aug_img,
                    [int(cv2.IMWRITE_JPEG_QUALITY), 92]
                )
                with open(os.path.join(labels_train, f"{aug_name}.txt"), "w") as f:
                    f.write(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
                cls_count += 1

        total_images += cls_count
        stats[cls_name] = cls_count
        print(f"  ✅ [{cls_name}] → {cls_count} ảnh (gốc + augmented)")

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

    # Tạo báo cáo
    print(f"\n{'='*60}")
    print(f" HOÀN TẤT XÂY DỰNG DATASET")
    print(f" Tổng ảnh: {total_images}")
    print(f" Train: {len(os.listdir(images_train))} | Val: {len(os.listdir(images_val))}")
    print(f" data.yaml: {yaml_path}")
    print(f"{'='*60}")
    print(f"\n Thống kê theo class:")
    for cls, count in stats.items():
        bar = "█" * min(count // 5, 30)
        print(f"   {cls:25s} → {count:4d} ảnh {bar}")

    return yaml_path


# ============================================================================
# HÀM KẾT HỢP: MERGE DATASET SYNTHETIC + REAL
# ============================================================================

def merge_datasets(synthetic_dir, real_dir, merged_dir):
    """
    Gộp dataset synthetic (ảnh vẽ) và real (ảnh thật) thành 1 dataset duy nhất.
    Giúp model vừa học từ ảnh vẽ (đặc trưng rõ ràng) vừa từ ảnh thật (chính xác thực tế).
    """
    merged_images_train = os.path.join(merged_dir, "images", "train")
    merged_images_val = os.path.join(merged_dir, "images", "val")
    merged_labels_train = os.path.join(merged_dir, "labels", "train")
    merged_labels_val = os.path.join(merged_dir, "labels", "val")

    for d in [merged_images_train, merged_images_val, merged_labels_train, merged_labels_val]:
        os.makedirs(d, exist_ok=True)

    copied = 0

    for source_dir, prefix in [(synthetic_dir, "syn"), (real_dir, "real")]:
        for split in ["train", "val"]:
            src_img = os.path.join(source_dir, "images", split)
            src_lbl = os.path.join(source_dir, "labels", split)
            dst_img = os.path.join(merged_dir, "images", split)
            dst_lbl = os.path.join(merged_dir, "labels", split)

            if not os.path.isdir(src_img):
                continue

            for fname in os.listdir(src_img):
                if not fname.lower().endswith(('.jpg', '.jpeg', '.png')):
                    continue
                base = os.path.splitext(fname)[0]
                new_name = f"{prefix}_{fname}" if not fname.startswith(prefix) else fname

                src_img_path = os.path.join(src_img, fname)
                src_lbl_path = os.path.join(src_lbl, f"{base}.txt")
                dst_img_path = os.path.join(dst_img, new_name)
                dst_lbl_path = os.path.join(dst_lbl, f"{prefix}_{base}.txt" if not base.startswith(prefix) else f"{base}.txt")

                if os.path.exists(src_img_path):
                    shutil.copy2(src_img_path, dst_img_path)
                if os.path.exists(src_lbl_path):
                    shutil.copy2(src_lbl_path, dst_lbl_path)
                copied += 1

    # Tạo data.yaml
    yaml_path = os.path.join(merged_dir, "data.yaml")
    clean_path = os.path.abspath(merged_dir).replace("\\", "/")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(f"path: {clean_path}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write("names:\n")
        for idx, name in enumerate(CLASSES):
            f.write(f"  {idx}: {name}\n")

    print(f"\n✅ Đã gộp {copied} ảnh vào {merged_dir}")
    print(f"   data.yaml: {yaml_path}")
    return yaml_path


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Tải ảnh thật mặt sau iPhone từ internet và tạo dataset YOLO"
    )
    parser.add_argument("--max-images", type=int, default=50,
                        help="Số ảnh tối đa tải cho mỗi dòng điện thoại (mặc định: 50)")
    parser.add_argument("--output", type=str, default="dataset_real_v1",
                        help="Tên thư mục dataset đầu ra (mặc định: dataset_real_v1)")
    parser.add_argument("--augment", type=int, default=3,
                        help="Số bản augment cho mỗi ảnh gốc (mặc định: 3)")
    parser.add_argument("--skip-download", action="store_true",
                        help="Bỏ qua bước tải ảnh, chỉ build dataset từ ảnh đã có")
    parser.add_argument("--merge-with-synthetic", action="store_true",
                        help="Gộp với dataset synthetic (ảnh vẽ) thành dataset cuối cùng")
    parser.add_argument("--synthetic-dir", type=str, default="dataset_clean_v4",
                        help="Thư mục dataset synthetic để merge")
    parser.add_argument("--classes", type=str, nargs="*", default=None,
                        help="Chỉ tải cho các class cụ thể (ví dụ: iphone-15-pro iphone-16-pro-max)")

    args = parser.parse_args()

    if not HAS_DEPS:
        print("\n❌ Thiếu thư viện! Chạy:")
        print("   pip install requests Pillow opencv-python numpy tqdm")
        sys.exit(1)

    service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    raw_dir = os.path.join(service_dir, "dataset_real_raw")
    output_dir = os.path.join(service_dir, args.output)

    # Bước 1: Tải ảnh thật
    if not args.skip_download:
        print(f"\n{'='*60}")
        print(f" BƯỚC 1: TẢI ẢNH THẬT TỪ INTERNET")
        print(f" Mỗi class: {args.max_images} ảnh")
        print(f"{'='*60}\n")

        classes_to_download = args.classes if args.classes else CLASSES
        for cls_name in classes_to_download:
            if cls_name not in PHONE_SEARCH_QUERIES:
                print(f"  ⚠ Không tìm thấy class: {cls_name}, bỏ qua.")
                continue
            queries = PHONE_SEARCH_QUERIES[cls_name]
            download_dataset_for_class(cls_name, queries, raw_dir, args.max_images)
            time.sleep(random.uniform(1, 3))

    # Bước 2: Build dataset YOLO
    print(f"\n BƯỚC 2: XÂY DỰNG DATASET YOLO")
    yaml_path = build_real_dataset(
        raw_dir, output_dir,
        augment_per_image=args.augment,
        target_size=640,
        val_ratio=0.2
    )

    # Bước 3 (Tùy chọn): Merge với synthetic
    if args.merge_with_synthetic:
        print(f"\n BƯỚC 3: GỘP VỚI DATASET SYNTHETIC")
        syn_dir = os.path.join(service_dir, args.synthetic_dir)
        merged_dir = os.path.join(service_dir, f"{args.output}_merged")
        if os.path.exists(syn_dir):
            yaml_path = merge_datasets(syn_dir, output_dir, merged_dir)
            print(f"\n 🎯 Dataset cuối cùng (merged): {merged_dir}")
            print(f"    Dùng file này để train: {yaml_path}")
        else:
            print(f"  ⚠ Không tìm thấy {syn_dir}. Bỏ qua merge.")

    # Hướng dẫn train
    print(f"\n{'='*60}")
    print(f" HƯỚNG DẪN TRAIN MODEL YOLO")
    print(f"{'='*60}")
    print(f"""
  1. Train trên dataset ảnh thật:
     cd AI_Service
     python train_yolo.py --data {os.path.basename(output_dir)}/data.yaml --epochs 50 --batch 8 --name iphone_real_v1

  2. Hoặc train trên dataset gộp (synthetic + real) - KHUYẾN NGHỊ:
     python tools/download_real_dataset.py --merge-with-synthetic
     python train_yolo.py --data {os.path.basename(output_dir)}_merged/data.yaml --epochs 50 --batch 8 --name iphone_merged_v1

  3. Weights sau khi train sẽ tự động lưu vào:
     AI_Service/weights/yolo_phone_detect.pt
""")


if __name__ == "__main__":
    main()
