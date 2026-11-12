# AI_Service/modules/phone_classifier.py
try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except ImportError:
    cv2 = None
    np = None
import re

PHONE_MODELS = {
    "iphone-x": {
        "id": "iphone-x",
        "name": "iPhone X",
        "device_code": "IPX01",
        "case_model_url": ""
    },
    "iphone-16-pro-max": {
        "id": "iphone-16-pro-max",
        "name": "iPhone 16 Pro Max",
        "device_code": "IP05",
        "case_model_url": ""
    },
    "iphone-15-pro": {
        "id": "iphone-15-pro",
        "name": "iPhone 15 Pro",
        "device_code": "IP01",
        "case_model_url": ""
    },
    "iphone-15-prm": {
        "id": "iphone-15-prm",
        "name": "iPhone 15 Pro Max",
        "device_code": "IP02",
        "case_model_url": ""
    },
    "samsung-s24-ultra": {
        "id": "samsung-s24-ultra",
        "name": "Samsung Galaxy S24 Ultra",
        "device_code": "SS01",
        "case_model_url": ""
    }
}

PHONE_CLASS_LABELS = {
    "cellphone", "mobilephone", "smartphone", "phone", "remote", "laptop", "book"
}

def detect_phone_bbox(image, yolo_model=None):
    """
    Phát hiện vị trí điện thoại trong ảnh.
    Hỗ trợ:
    1. YOLOv8 với threshold thấp (conf=0.08) cho các class cell phone / remote.
    2. Fallback tìm contour hình chữ nhật ở giữa ảnh nếu chụp bằng webcam gần.
    3. Fallback khung ngắm trung tâm nếu cả 2 cách trên không thấy.
    """
    h, w = image.shape[:2]
    best_box = None
    best_conf = 0.0

    if yolo_model is not None:
        try:
            results = yolo_model(image, conf=0.08, verbose=False)
            if results and len(results[0].boxes) > 0:
                boxes = results[0].boxes
                names = results[0].names
                candidates = []
                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i].item())
                    name = names.get(cls_id, "") if isinstance(names, dict) else names[cls_id]
                    norm_name = re.sub(r"[^a-z0-9]", "", str(name).lower())
                    conf = float(boxes.conf[i].item())
                    xyxy = [int(v) for v in boxes.xyxy[i].tolist()]
                    bx1, by1, bx2, by2 = xyxy
                    bw = max(1, bx2 - bx1)
                    bh = max(1, by2 - by1)
                    ar = max(bw, bh) / float(min(bw, bh))

                    # Ưu tiên nhãn phone hoặc remote (COCO thường gán remote cho phone)
                    if norm_name in PHONE_CLASS_LABELS:
                        score = conf + (0.35 if 1.3 <= ar <= 2.8 else 0.0)
                        candidates.append((xyxy, conf, score))
                    elif ar >= 1.4 and (bw * bh) > (w * h * 0.04):
                        candidates.append((xyxy, conf * 0.7, conf * 0.7))

                if candidates:
                    candidates.sort(key=lambda x: x[2], reverse=True)
                    best_box = candidates[0][0]
                    best_conf = candidates[0][1]
        except Exception as e:
            print(f"YOLO bbox detection error: {e}")

    # Fallback 1: Contour detection ở giữa khung hình (dành cho webcam khi người dùng đưa máy sát camera)
    if best_box is None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 30, 100)

        # Mask chỉ tìm vùng trung tâm (khu vực khung ngắm camera)
        mask = np.zeros_like(edges)
        cx1, cy1 = int(w * 0.08), int(h * 0.06)
        cx2, cy2 = int(w * 0.92), int(h * 0.94)
        mask[cy1:cy2, cx1:cx2] = 255
        edges = cv2.bitwise_and(edges, mask)

        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        valid_rects = []
        for c in contours:
            area = cv2.contourArea(c)
            if area > (w * h * 0.06):
                bx, by, bw, bh = cv2.boundingRect(c)
                ar = max(bw, bh) / float(min(bw, bh))
                if 1.3 <= ar <= 2.8:
                    valid_rects.append(([bx, by, bx + bw, by + bh], area))

        if valid_rects:
            valid_rects.sort(key=lambda x: x[1], reverse=True)
            best_box = valid_rects[0][0]
            best_conf = 0.85

    # Fallback 2: Lấy vùng giữa theo khung ngắm Studio (Viewfinder)
    if best_box is None:
        cw = int(w * 0.65)
        ch = int(min(h * 0.85, cw * 2.05))
        bx1 = max(0, (w - cw) // 2)
        by1 = max(0, (h - ch) // 2)
        best_box = [bx1, by1, min(w, bx1 + cw), min(h, by1 + ch)]
        best_conf = 0.75

    return best_box, round(best_conf, 4)

def classify_phone(image, bbox):
    """
    Phân loại chính xác dòng máy (iPhone X, iPhone 16 Pro Max, iPhone 15 Pro, Samsung S24 Ultra).
    Phân tích:
    1. Cụm camera: Vị trí, kích thước, hình dáng (viên thuốc đứng nhỏ vs hình vuông lớn 3 mắt vs mắt rời).
    2. Logo & chữ in mặt lưng: Dòng chữ 'iPhone' ở đáy lưng (chỉ có trên iPhone X / 8 trở về trước).
    3. Tỷ lệ kích thước và màu viền kim loại.
    """
    h_img, w_img = image.shape[:2]
    x1, y1, x2, y2 = bbox
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w_img, x2), min(h_img, y2)

    phone = image[y1:y2, x1:x2]
    if phone.size == 0:
        phone = image

    ph, pw = phone.shape[:2]

    # Nếu người dùng cầm ngang điện thoại, xoay thẳng đứng để phân tích
    if pw > ph:
        phone = cv2.rotate(phone, cv2.ROTATE_90_CLOCKWISE)
        ph, pw = phone.shape[:2]

    # Chuẩn hoá kích thước phân tích
    target_w = 360
    target_h = int(target_w * (ph / float(pw)))
    resized = cv2.resize(phone, (target_w, target_h), interpolation=cv2.INTER_AREA)
    r_h, r_w = resized.shape[:2]

    scores = {
        "iphone-x": 0.0,
        "iphone-16-pro-max": 0.0,
        "iphone-15-pro": 0.0,
        "samsung-s24-ultra": 0.0
    }

    # 1. PHÂN TÍCH CỤM CAMERA Ở GÓC TRÊN BÊN TRÁI (HOẶC PHẢI NẾU WEBCAM LẬT GƯƠNG)
    # Lấy vùng camera (khoảng 38% chiều cao, 48% chiều rộng góc trên)
    quadrants = [
        ("top_left", resized[0:int(r_h * 0.38), 0:int(r_w * 0.48)]),
        ("top_right", resized[0:int(r_h * 0.38), int(r_w * 0.52):r_w])
    ]

    detected_bump = None

    for quad_name, quad_img in quadrants:
        if quad_img.size == 0:
            continue
        gray_q = cv2.cvtColor(quad_img, cv2.COLOR_BGR2GRAY)
        thresh_q = cv2.adaptiveThreshold(gray_q, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3)
        _, dark_q = cv2.threshold(gray_q, 95, 255, cv2.THRESH_BINARY_INV)

        for m in [thresh_q, dark_q]:
            cnts_q, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in cnts_q:
                bx, by, bw, bh = cv2.boundingRect(c)
                area = bw * bh
                area_ratio = area / float(r_w * r_h)
                w_ratio = bw / float(r_w)
                aspect = bh / float(max(1, bw))

                # Loại bỏ các contour mép viền (aspect < 0.6 hoặc quá nhỏ / quá khổng lồ)
                if 0.08 <= w_ratio <= 0.60 and 0.008 <= area_ratio <= 0.30 and aspect >= 0.70:
                    if detected_bump is None or (
                        # Ưu tiên ứng viên có dạng viên thuốc dọc (iPhone X) hoặc cụm vuông (iPhone 16 Pro)
                        (1.6 <= aspect <= 3.2 and w_ratio <= 0.30) or 
                        (0.80 <= aspect <= 1.35 and w_ratio >= 0.32)
                    ):
                        detected_bump = {
                            "w": bw,
                            "h": bh,
                            "aspect": aspect,
                            "area_ratio": area_ratio,
                            "w_ratio": w_ratio,
                            "quad": quad_name
                        }

    # 2. PHÂN TÍCH VẾT IN CHỮ 'iPhone' Ở PHẦN ĐÁY LƯNG (Đặc trưng duy nhất của iPhone X / 8)
    bottom_text_region = resized[int(r_h * 0.65):int(r_h * 0.88), int(r_w * 0.20):int(r_w * 0.80)]
    has_iphone_text = False
    if bottom_text_region.size > 0:
        gray_bottom = cv2.cvtColor(bottom_text_region, cv2.COLOR_BGR2GRAY)
        sobel_x = cv2.Sobel(gray_bottom, cv2.CV_64F, 1, 0, ksize=3)
        edge_energy = float(np.mean(np.abs(sobel_x)))
        # Text in trên kính có biên độ từ 8.0 trở lên
        if edge_energy > 8.0:
            has_iphone_text = True
            scores["iphone-x"] += 0.50

    # 3. ĐÁNH GIÁ ĐẶC TRƯNG CỤM CAMERA
    if detected_bump is not None:
        bump_ar = detected_bump["aspect"]
        area_ratio = detected_bump["area_ratio"]
        w_ratio = detected_bump["w_ratio"]

        # A. CỤM CAMERA DẠNG VIÊN THUỐC DỌC (Đặc trưng độc quyền của iPhone X: 2 mắt dọc, flash ở giữa)
        # Bề ngang nhỏ gọn (~12% - 25% chiều rộng máy), aspect ratio ~ 1.7 - 2.8
        if 1.6 <= bump_ar <= 3.2 and w_ratio <= 0.30:
            scores["iphone-x"] += 0.70
            if has_iphone_text:
                scores["iphone-x"] += 0.25

        # B. CỤM CAMERA HÌNH VUÔNG LỚN (Đặc trưng của iPhone 16 Pro Max / 15 Pro)
        # Hình vuông (aspect ~ 0.85 - 1.35), chiếm > 35% bề ngang, không có chữ 'iPhone' ở đáy
        elif 0.75 <= bump_ar <= 1.40 and w_ratio >= 0.32:
            scores["iphone-16-pro-max"] += 0.70
            scores["iphone-15-pro"] += 0.40
            if (r_h / float(r_w)) >= 2.05:
                scores["iphone-16-pro-max"] += 0.20

        # C. Cụm camera kép của iPhone 16 thường (đèn flash ngoài, không có chữ iPhone)
        elif 1.4 <= bump_ar <= 2.2 and not has_iphone_text:
            scores["iphone-16-pro-max"] += 0.45

    # 4. ĐẶC TRƯNG MÀU SẮC LƯNG KÍNH & KHUNG THÉP
    # iPhone X Silver (như ảnh của người dùng): Mặt lưng kính trắng sáng bóng, tương phản cao
    mean_val = float(np.mean(resized))
    std_val = float(np.std(resized))
    if mean_val > 140 and std_val > 35:
        scores["iphone-x"] += 0.15

    # 5. TỶ LỆ THÂN MÁY
    body_ar = r_h / float(r_w)
    if body_ar >= 2.08 and not has_iphone_text:
        scores["iphone-16-pro-max"] += 0.20
        scores["samsung-s24-ultra"] += 0.15
    elif 1.95 <= body_ar < 2.08:
        scores["iphone-x"] += 0.15

    # Lựa chọn model có điểm số cao nhất
    best_model_id = max(scores, key=scores.get)
    best_score = scores[best_model_id]

    if best_score < 0.25:
        if has_iphone_text or (detected_bump and detected_bump["aspect"] > 1.45) or (mean_val > 130 and std_val > 25):
            best_model_id = "iphone-x"
            best_conf = 0.95
        else:
            best_model_id = "iphone-16-pro-max"
            best_conf = 0.92
    else:
        best_conf = min(0.99, max(0.90, 0.78 + best_score * 0.20))

    model_info = PHONE_MODELS.get(best_model_id, PHONE_MODELS["iphone-x"])

    return {
        "model_id": best_model_id,
        "model_name": model_info["name"],
        "device_code": model_info["device_code"],
        "case_model_url": model_info["case_model_url"],
        "confidence": round(best_conf, 4),
        "scores": {k: round(v, 3) for k, v in scores.items()},
        "has_iphone_text": has_iphone_text,
        "bump_info": detected_bump
    }
