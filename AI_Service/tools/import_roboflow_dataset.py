# AI_Service/tools/import_roboflow_dataset.py
"""
Script nhập dataset từ Roboflow Universe hoặc Kaggle vào cấu trúc YOLO của project.

Roboflow Universe có nhiều dataset iPhone detection miễn phí:
  - Tìm kiếm: https://universe.roboflow.com/search?q=iphone+back
  - Export format: YOLOv8

Cách dùng:
    1. Tải dataset từ Roboflow (chọn format YOLOv8, download ZIP)
    2. Giải nén vào thư mục tạm (ví dụ: AI_Service/imported_roboflow/)
    3. Chạy script này:
       python tools/import_roboflow_dataset.py --source imported_roboflow --output dataset_roboflow_v1

    Hoặc dùng Roboflow Python API (cần API key miễn phí):
       python tools/import_roboflow_dataset.py --api-key YOUR_KEY --workspace YOUR_WS --project YOUR_PROJECT --version 1
"""

import os
import sys
import shutil
import argparse
import json

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

# Mapping tên class từ các dataset phổ biến sang class name của project
CLASS_MAPPING = {
    # Tên có thể xuất hiện trong dataset Roboflow/Kaggle
    "iphone_x": "iphone-x",
    "iphonex": "iphone-x",
    "iphone-x": "iphone-x",
    "iphone_xs": "iphone-x",
    "iphone_xr": "iphone-xr",
    "iphonexr": "iphone-xr",
    "iphone-xr": "iphone-xr",
    "iphone_11": "iphone-11",
    "iphone11": "iphone-11",
    "iphone-11": "iphone-11",
    "iphone_11_pro_max": "iphone-11-prm",
    "iphone11promax": "iphone-11-prm",
    "iphone-11-pro-max": "iphone-11-prm",
    "iphone-11-prm": "iphone-11-prm",
    "iphone_12": "iphone-12",
    "iphone12": "iphone-12",
    "iphone-12": "iphone-12",
    "iphone_12_pro_max": "iphone-12-prm",
    "iphone12promax": "iphone-12-prm",
    "iphone-12-pro-max": "iphone-12-prm",
    "iphone-12-prm": "iphone-12-prm",
    "iphone_13": "iphone-13",
    "iphone13": "iphone-13",
    "iphone-13": "iphone-13",
    "iphone_13_pro_max": "iphone-13-prm",
    "iphone13promax": "iphone-13-prm",
    "iphone-13-pro-max": "iphone-13-prm",
    "iphone-13-prm": "iphone-13-prm",
    "iphone_14_pro_max": "iphone-14-prm",
    "iphone14promax": "iphone-14-prm",
    "iphone-14-pro-max": "iphone-14-prm",
    "iphone-14-prm": "iphone-14-prm",
    "iphone_15_pro": "iphone-15-pro",
    "iphone15pro": "iphone-15-pro",
    "iphone-15-pro": "iphone-15-pro",
    "iphone_16_pro_max": "iphone-16-pro-max",
    "iphone16promax": "iphone-16-pro-max",
    "iphone-16-pro-max": "iphone-16-pro-max",
    "iphone_18_pro_max": "iphone-18-prm",
    "iphone18promax": "iphone-18-prm",
    "iphone-18-pro-max": "iphone-18-prm",
    "iphone-18-prm": "iphone-18-prm",
    # Generic phone labels
    "cell phone": None,
    "cellphone": None,
    "phone": None,
    "smartphone": None,
    "mobile phone": None,
}

CLASSES = [
    "iphone-x", "iphone-xr", "iphone-11", "iphone-11-prm",
    "iphone-12", "iphone-12-prm", "iphone-13", "iphone-13-prm",
    "iphone-14-prm", "iphone-15-pro", "iphone-16-pro-max",
    "iphone-18-prm"
]


def import_from_folder(source_dir, output_dir):
    """
    Import dataset từ thư mục đã giải nén (Roboflow YOLOv8 format).
    Cấu trúc mong đợi:
        source_dir/
        ├── train/images/    (hoặc images/train/)
        ├── train/labels/    (hoặc labels/train/)
        ├── valid/images/
        ├── valid/labels/
        └── data.yaml
    """
    # Tìm data.yaml
    yaml_path = None
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            if f == "data.yaml":
                yaml_path = os.path.join(root, f)
                break
        if yaml_path:
            break

    # Đọc class names từ data.yaml nếu có
    source_classes = {}
    if yaml_path:
        print(f"  📄 Tìm thấy data.yaml: {yaml_path}")
        with open(yaml_path, "r") as f:
            content = f.read()
        # Parse names đơn giản
        import re
        for match in re.finditer(r"(\d+):\s*(.+)", content):
            cls_id = int(match.group(1))
            cls_name = match.group(2).strip().lower().replace(" ", "_")
            source_classes[cls_id] = cls_name

    if source_classes:
        print(f"  📋 Classes trong dataset nguồn: {source_classes}")

    # Tìm thư mục images
    possible_structures = [
        ("train/images", "train/labels", "valid/images", "valid/labels"),
        ("images/train", "labels/train", "images/val", "labels/val"),
        ("train", "train", "valid", "valid"),  # labels cùng thư mục
    ]

    found = False
    for train_img, train_lbl, val_img, val_lbl in possible_structures:
        ti = os.path.join(source_dir, train_img)
        tl = os.path.join(source_dir, train_lbl)
        if os.path.isdir(ti):
            found = True
            _copy_and_remap(ti, tl, os.path.join(source_dir, val_img),
                           os.path.join(source_dir, val_lbl),
                           output_dir, source_classes)
            break

    if not found:
        print("  ⚠ Không tìm thấy cấu trúc dataset chuẩn. Hãy kiểm tra lại thư mục nguồn.")
        return None

    # Tạo data.yaml mới
    yaml_out = os.path.join(output_dir, "data.yaml")
    clean_path = os.path.abspath(output_dir).replace("\\", "/")
    with open(yaml_out, "w", encoding="utf-8") as f:
        f.write(f"path: {clean_path}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write("names:\n")
        for idx, name in enumerate(CLASSES):
            f.write(f"  {idx}: {name}\n")

    print(f"\n✅ Import hoàn tất! data.yaml: {yaml_out}")
    return yaml_out


def _copy_and_remap(train_img_dir, train_lbl_dir, val_img_dir, val_lbl_dir,
                    output_dir, source_classes):
    """Copy ảnh và remap class IDs."""
    class_to_id = {cls: idx for idx, cls in enumerate(CLASSES)}

    for split, img_dir, lbl_dir in [("train", train_img_dir, train_lbl_dir),
                                     ("val", val_img_dir, val_lbl_dir)]:
        out_img = os.path.join(output_dir, "images", split)
        out_lbl = os.path.join(output_dir, "labels", split)
        os.makedirs(out_img, exist_ok=True)
        os.makedirs(out_lbl, exist_ok=True)

        if not os.path.isdir(img_dir):
            continue

        copied = 0
        for fname in os.listdir(img_dir):
            if not fname.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                continue

            base = os.path.splitext(fname)[0]
            lbl_file = os.path.join(lbl_dir, f"{base}.txt")

            # Copy ảnh
            shutil.copy2(os.path.join(img_dir, fname), os.path.join(out_img, fname))

            # Remap labels nếu cần
            if os.path.exists(lbl_file):
                with open(lbl_file, "r") as f:
                    lines = f.readlines()

                new_lines = []
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        old_cls_id = int(parts[0])
                        old_cls_name = source_classes.get(old_cls_id, "")

                        # Tìm class tương ứng trong project
                        mapped_name = CLASS_MAPPING.get(old_cls_name)
                        if mapped_name and mapped_name in class_to_id:
                            new_cls_id = class_to_id[mapped_name]
                            new_lines.append(f"{new_cls_id} {' '.join(parts[1:])}\n")
                        elif old_cls_name in class_to_id:
                            new_lines.append(line)
                        # Bỏ qua class không mapping được

                if new_lines:
                    with open(os.path.join(out_lbl, f"{base}.txt"), "w") as f:
                        f.writelines(new_lines)

            copied += 1

        print(f"  [{split}] Đã copy {copied} ảnh")


def import_from_roboflow_api(api_key, workspace, project, version, output_dir):
    """Import trực tiếp từ Roboflow API."""
    try:
        from roboflow import Roboflow
    except ImportError:
        print("  Cài đặt roboflow: pip install roboflow")
        sys.exit(1)

    rf = Roboflow(api_key=api_key)
    proj = rf.workspace(workspace).project(project)
    dataset = proj.version(version).download("yolov8", location=output_dir)
    print(f"  ✅ Đã tải dataset từ Roboflow → {output_dir}")

    # Remap nếu cần
    return import_from_folder(output_dir, output_dir + "_remapped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Import dataset từ Roboflow/Kaggle")
    parser.add_argument("--source", type=str, help="Thư mục nguồn đã giải nén")
    parser.add_argument("--output", type=str, default="dataset_imported",
                        help="Thư mục output")
    parser.add_argument("--api-key", type=str, help="Roboflow API key")
    parser.add_argument("--workspace", type=str, help="Roboflow workspace")
    parser.add_argument("--project", type=str, help="Roboflow project")
    parser.add_argument("--version", type=int, default=1, help="Roboflow version")

    args = parser.parse_args()

    service_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(service_dir, args.output)

    if args.api_key and args.workspace and args.project:
        import_from_roboflow_api(args.api_key, args.workspace, args.project,
                                 args.version, output_path)
    elif args.source:
        source_path = os.path.join(service_dir, args.source) if not os.path.isabs(args.source) else args.source
        import_from_folder(source_path, output_path)
    else:
        print("Cần chỉ định --source hoặc --api-key/--workspace/--project")
        parser.print_help()
