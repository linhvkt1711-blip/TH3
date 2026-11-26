# AI_Service/modules/phone_classifier.py
import os
import sys
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
        "name": "iPhone X / Xs (iPhone 10)",
        "device_code": "IPX01",
        "case_model_url": "/models/cases/iphone-x/scene.gltf"
    },
    "iphone-11": {
        "id": "iphone-11",
        "name": "iPhone 11",
        "device_code": "IP11",
        "case_model_url": ""
    },
    "iphone-11-prm": {
        "id": "iphone-11-prm",
        "name": "iPhone 11 Pro Max",
        "device_code": "IP11PM",
        "case_model_url": ""
    },
    "iphone-12": {
        "id": "iphone-12",
        "name": "iPhone 12",
        "device_code": "IP12",
        "case_model_url": ""
    },
    "iphone-12-prm": {
        "id": "iphone-12-prm",
        "name": "iPhone 12 Pro Max",
        "device_code": "IP12PM",
        "case_model_url": ""
    },
    "iphone-13": {
        "id": "iphone-13",
        "name": "iPhone 13",
        "device_code": "IP13",
        "case_model_url": ""
    },
    "iphone-13-prm": {
        "id": "iphone-13-prm",
        "name": "iPhone 13 Pro Max",
        "device_code": "IP13PM",
        "case_model_url": ""
    },
    "iphone-14-prm": {
        "id": "iphone-14-prm",
        "name": "iPhone 14 Pro Max",
        "device_code": "IP14PM",
        "case_model_url": ""
    },
    "iphone-15-pro": {
        "id": "iphone-15-pro",
        "name": "iPhone 15 Pro",
        "device_code": "IP01",
        "case_model_url": ""
    },
    "iphone-16-pro-max": {
        "id": "iphone-16-pro-max",
        "name": "iPhone 16 Pro Max",
        "device_code": "IP05",
        "case_model_url": ""
    },
    "iphone-17-prm": {
        "id": "iphone-17-prm",
        "name": "iPhone 17 Pro Max",
        "device_code": "IP17PM",
        "case_model_url": ""
    },
    "iphone-18-prm": {
        "id": "iphone-18-prm",
        "name": "iPhone 18 Pro Max",
        "device_code": "IP18PM",
        "case_model_url": ""
    },
    "redmi-note-10-pro": {
        "id": "redmi-note-10-pro",
        "name": "Xiaomi Redmi Note 10 Pro",
        "device_code": "RMN10P",
        "case_model_url": ""
    }
}

REFERENCE_TEMPLATES = []
_ORB_DETECTOR = None

def _get_orb():
    global _ORB_DETECTOR
    if _ORB_DETECTOR is None and cv2 is not None:
        _ORB_DETECTOR = cv2.ORB_create(nfeatures=400)
    return _ORB_DETECTOR

def _extract_top_camera_orb(bgr_img):
    """Trích xuất ORB descriptors ở nửa trên (vùng camera) để kháng nứt/bể phần lưng dưới."""
    orb = _get_orb()
    if orb is None or bgr_img is None or bgr_img.size == 0:
        return None
    h, w = bgr_img.shape[:2]
    tw = 320
    th = max(60, int(tw * (h / float(max(1, w)))))
    resized = cv2.resize(bgr_img, (tw, th), interpolation=cv2.INTER_AREA)
    top_roi = resized[0:int(th * 0.52), :]
    gray = cv2.cvtColor(top_roi, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)  # Giảm nhiễu vết nứt mảnh
    _, des = orb.detectAndCompute(gray, None)
    return des

def _build_template_entry(fname, model_id, im):
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
    cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
    gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    small = cv2.resize(gray, (64, 64))
    orb_des = _extract_top_camera_orb(im)
    return (fname, model_id, hist, small, orb_des)

def init_reference_templates():
    global REFERENCE_TEMPLATES
    if REFERENCE_TEMPLATES:
        return
    ref_mapping = {
        "Iphone X (2).jpg": "iphone-x",
        "iphone x.jpg": "iphone-x",
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
        "iphone 18 pro.png": "iphone-18-prm"
    }
    extracted_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "user_uploaded_extracted")
    if os.path.exists(extracted_dir):
        for fname, model_id in ref_mapping.items():
            p = os.path.join(extracted_dir, fname)
            if os.path.exists(p):
                im = cv2.imread(p)
                if im is not None:
                    REFERENCE_TEMPLATES.append(_build_template_entry(fname, model_id, im))

        # Tự động nạp thêm ảnh mẫu Redmi Note 10 Pro nếu có trong user_uploaded_extracted/ hoặc thư mục con redmi-note-10-pro/
        extra_dirs = [
            (extracted_dir, lambda f: "redmi" in f.lower()),
            (os.path.join(extracted_dir, "redmi-note-10-pro"), lambda f: f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
        ]
        for folder, pred in extra_dirs:
            if os.path.isdir(folder):
                for fname in os.listdir(folder):
                    if pred(fname) and fname.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                        p = os.path.join(folder, fname)
                        im = cv2.imread(p)
                        if im is not None:
                            REFERENCE_TEMPLATES.append(_build_template_entry(fname, "redmi-note-10-pro", im))

def match_reference_template(image):
    init_reference_templates()
    if not REFERENCE_TEMPLATES:
        return None, 0.0

    try:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        hist = cv2.calcHist([hsv], [0, 1], None, [16, 16], [0, 180, 0, 256])
        cv2.normalize(hist, hist, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        test_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        test_small = cv2.resize(test_gray, (64, 64))
        test_orb_des = _extract_top_camera_orb(image)
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False) if test_orb_des is not None else None

        best_score = -1.0
        best_id = None
        for _, mid, ref_hist, ref_small, ref_orb_des in REFERENCE_TEMPLATES:
            color_sim = cv2.compareHist(hist, ref_hist, cv2.HISTCMP_CORREL)
            shape_sim = cv2.matchTemplate(test_small, ref_small, cv2.TM_CCOEFF_NORMED)[0][0]
            total_score = 0.5 * color_sim + 0.5 * shape_sim

            # Nếu ảnh bị nứt/bể phần dưới, ORB ở vùng camera trên vẫn cứu được điểm khớp cục bộ
            if bf is not None and ref_orb_des is not None and len(ref_orb_des) >= 10 and len(test_orb_des) >= 10:
                try:
                    knn = bf.knnMatch(test_orb_des, ref_orb_des, k=2)
                    good = [m for pair in knn if len(pair) == 2 for m, n in [pair] if m.distance < 0.75 * n.distance]
                    orb_score = min(1.0, len(good) / 28.0)
                    if orb_score > 0.45:
                        total_score = max(total_score, 0.30 * color_sim + 0.70 * orb_score)
                except Exception:
                    pass

            if total_score > best_score:
                best_score = total_score
                best_id = mid

        if best_score >= 0.70:
            return best_id, best_score
    except Exception as e:
        print(f"Lỗi match template: {e}")

    return None, 0.0

GENERIC_PHONE_LABELS = {
    "cellphone", "mobilephone", "smartphone", "phone", "remote", "laptop", "book"
}

def detect_phone_bbox(image, yolo_model=None):
    """
    Phát hiện vị trí điện thoại trong ảnh.
    Hỗ trợ:
    1. Nếu yolo_model là custom weights đã train dòng máy:
       Trả về bounding box và class_id trực tiếp với độ chính xác cao.
    2. Nếu yolo_model là weights gốc COCO:
       Tìm box nhãn 'cell phone' / 'remote' với threshold tối ưu.
    3. Fallback Contour detection ở giữa khung hình.
    4. Fallback khung ngắm trung tâm nếu camera chụp góc hẹp.

    Trả về: (best_box, best_conf, recognized_model_id)
    """
    h, w = image.shape[:2]
    best_box = None
    best_conf = 0.0
    recognized_model_id = None

    if yolo_model is not None:
        try:
            # Ngưỡng 0.15 giúp bắt nhạy cả ảnh camera thực tế và ảnh tải lên
            results = yolo_model(image, conf=0.15, verbose=False)
            if results and len(results[0].boxes) > 0:
                boxes = results[0].boxes
                names = results[0].names
                candidates = []

                for i in range(len(boxes)):
                    cls_id = int(boxes.cls[i].item())
                    name = names.get(cls_id, "") if isinstance(names, dict) else names[cls_id]
                    norm_name = str(name).lower().strip()
                    conf = float(boxes.conf[i].item())
                    xyxy = [int(v) for v in boxes.xyxy[i].tolist()]
                    bx1, by1, bx2, by2 = xyxy
                    bw = max(1, bx2 - bx1)
                    bh = max(1, by2 - by1)
                    ar = max(bw, bh) / float(min(bw, bh))

                    # Trường hợp A: Model YOLO đã được huấn luyện riêng từng dòng điện thoại
                    if norm_name in PHONE_MODELS:
                        score = conf + 0.50 + (0.20 if 1.2 <= ar <= 3.0 else 0.0)
                        candidates.append((xyxy, conf, score, norm_name))

                    elif norm_name.startswith(("iphone-", "samsung-")):
                        score = conf + 0.50 + (0.20 if 1.2 <= ar <= 3.0 else 0.0)
                        candidates.append((xyxy, conf, score, norm_name))

                    # Trường hợp B: Model YOLO COCO chung (cell phone, remote)
                    elif re.sub(r"[^a-z0-9]", "", norm_name) in GENERIC_PHONE_LABELS:
                        score = conf + (0.35 if 1.2 <= ar <= 3.0 else 0.0)
                        candidates.append((xyxy, conf, score, None))

                if candidates:
                    candidates.sort(key=lambda x: x[2], reverse=True)
                    best_box = candidates[0][0]
                    best_conf = candidates[0][1]
                    recognized_model_id = candidates[0][3]
        except Exception as e:
            print(f"Lỗi inference YOLO bbox: {e}")

    # Contour fallback is only used when YOLO is unavailable; a loaded model
    # with no detections must not turn a background or person into a phone.
    if best_box is None and yolo_model is None:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        edges = cv2.Canny(blurred, 30, 100)

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

    # Fallback an toàn cho ảnh tải lên trực tiếp (toàn bộ khung hình)
    if best_box is None:
        best_box = [0, 0, w, h]
        best_conf = 0.80

    return best_box, best_conf, recognized_model_id

def _detect_camera_bump_candidates(resized):
    """Phân tích cụm camera ở nửa trên mặt lưng (kháng vết nứt & hỗ trợ lật gương)."""
    r_h, r_w = resized.shape[:2]
    quadrants = [
        ("top_left", resized[0:int(r_h * 0.42), 0:int(r_w * 0.50)]),
        ("top_right", resized[0:int(r_h * 0.42), int(r_w * 0.50):r_w])
    ]

    best_bump = None
    best_redmi_bump = None
    close_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))

    for quad_name, quad_img in quadrants:
        if quad_img.size == 0:
            continue
        gray_q = cv2.cvtColor(quad_img, cv2.COLOR_BGR2GRAY)
        # Lọc trung vị để làm mờ các đường nứt mảnh nhưng giữ nguyên biên cụm camera
        smooth_q = cv2.medianBlur(gray_q, 5)
        thresh_q = cv2.adaptiveThreshold(smooth_q, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3)
        _, dark_q = cv2.threshold(smooth_q, 95, 255, cv2.THRESH_BINARY_INV)

        # Hàn liền cụm camera nếu bị vết nứt cắt ngang
        thresh_q = cv2.morphologyEx(thresh_q, cv2.MORPH_CLOSE, close_kernel)
        dark_q = cv2.morphologyEx(dark_q, cv2.MORPH_CLOSE, close_kernel)

        for m in [thresh_q, dark_q]:
            cnts_q, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in cnts_q:
                bx, by, bw, bh = cv2.boundingRect(c)
                area = bw * bh
                area_ratio = area / float(r_w * r_h)
                w_ratio = bw / float(r_w)
                aspect = bh / float(max(1, bw))

                if 0.08 <= w_ratio <= 0.60 and 0.008 <= area_ratio <= 0.30 and aspect >= 0.70:
                    candidate = {
                        "w": bw,
                        "h": bh,
                        "aspect": aspect,
                        "area_ratio": area_ratio,
                        "w_ratio": w_ratio,
                        "quad": quad_name
                    }
                    # Lưu riêng ứng viên cụm camera 2 tầng dọc (Redmi Note 10 Pro)
                    if 1.42 <= aspect <= 2.35 and 0.20 <= w_ratio <= 0.45 and area_ratio >= 0.025:
                        if best_redmi_bump is None or area_ratio > best_redmi_bump["area_ratio"]:
                            best_redmi_bump = candidate

                    if best_bump is None or area_ratio > best_bump["area_ratio"]:
                        best_bump = candidate

    return best_redmi_bump or best_bump, best_redmi_bump is not None


def classify_phone(image, bbox, direct_model_id=None, direct_confidence=0.0):
    """
    Phân loại chi tiết dòng điện thoại từ ảnh mặt lưng.
    Kết hợp mô hình học sâu YOLOv8 và kiểm chứng quang học (Optical Feature Verification):
    1. So khớp mẫu thực tế chuẩn từ tập dữ liệu người dùng cung cấp.
    2. Nhận diện cụm 2 camera kép xếp chéo (diagonal) -> iPhone 13.
    3. Nhận diện cụm 2 camera kép xếp dọc (vertical) -> iPhone 11 / 12.
    4. Nhận diện cụm 3 camera tam giác lớn & màu titan -> iPhone Pro / Pro Max.
    5. Nhận diện cụm camera viên thuốc dọc & chữ iPhone -> iPhone X.
    6. Nhận diện cụm camera chữ nhật 2 tầng dọc 108MP -> Xiaomi Redmi Note 10 Pro.
    """
    # 0. ƯU TIÊN 1: So khớp mẫu thực tế chuẩn xác (bao gồm cả ảnh mẫu Redmi nếu có)
    matched_id, matched_score = match_reference_template(image)
    if matched_id and matched_id in PHONE_MODELS:
        if matched_score >= 0.78 or not direct_model_id:
            info = PHONE_MODELS[matched_id]
            return {
                "model_id": info["id"],
                "model_name": info["name"],
                "device_code": info["device_code"],
                "case_model_url": info["case_model_url"],
                "confidence": round(float(matched_score), 4)
            }

    h_img, w_img = image.shape[:2]
    x1, y1, x2, y2 = bbox if bbox is not None else (0, 0, w_img, h_img)
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w_img, x2), min(h_img, y2)

    phone = image[y1:y2, x1:x2]
    if phone.size == 0:
        phone = image

    ph, pw = phone.shape[:2]

    # Xoay thẳng đứng nếu ảnh đang nằm ngang
    if pw > ph:
        phone = cv2.rotate(phone, cv2.ROTATE_90_CLOCKWISE)
        ph, pw = phone.shape[:2]

    target_w = 360
    target_h = int(target_w * (ph / float(max(1, pw))))
    resized = cv2.resize(phone, (target_w, target_h), interpolation=cv2.INTER_AREA)
    r_h, r_w = resized.shape[:2]

    # Kiểm chứng quang học cụm camera trước khi chấp nhận nhãn direct_model_id từ YOLO
    detected_bump, has_redmi_vertical_bump = _detect_camera_bump_candidates(resized)

    if direct_model_id:
        # Nếu YOLO (vốn train trên iPhone) đoán là iPhone nhưng cụm camera là chữ nhật dọc 2 tầng -> sửa thành Redmi Note 10 Pro
        if has_redmi_vertical_bump and direct_model_id.startswith("iphone-"):
            info = PHONE_MODELS["redmi-note-10-pro"]
            return {
                "model_id": info["id"],
                "model_name": info["name"],
                "device_code": info["device_code"],
                "case_model_url": info["case_model_url"],
                "confidence": round(max(0.82, float(direct_confidence)), 4)
            }

        info = PHONE_MODELS.get(direct_model_id)
        if info is None:
            return None
        return {
            "model_id": info["id"],
            "model_name": info["name"],
            "device_code": info["device_code"],
            "case_model_url": info["case_model_url"],
            "confidence": round(float(direct_confidence), 4)
        }

    # Kiểm tra cụm 2 camera kép chéo (iPhone 13) vs thẳng dọc (iPhone 12/11)
    # Vùng camera góc trên
    cam_roi = resized[int(r_h * 0.03):int(r_h * 0.38), int(r_w * 0.06):int(r_w * 0.55)]
    is_diagonal_camera = False
    if cam_roi.size > 0:
        cam_gray = cv2.medianBlur(cv2.cvtColor(cam_roi, cv2.COLOR_BGR2GRAY), 5)
        circles = cv2.HoughCircles(cam_gray, cv2.HOUGH_GRADIENT, dp=1.2, minDist=20, param1=45, param2=20, minRadius=10, maxRadius=60)
        if circles is not None and len(circles[0]) >= 2:
            c_sorted = sorted(circles[0], key=lambda x: x[1]) # Sắp xếp theo y
            c1, c2 = c_sorted[0], c_sorted[1]
            dx = abs(c1[0] - c2[0])
            dy = abs(c1[1] - c2[1])
            # Nếu 2 camera lệch cả trục ngang và trục dọc rõ rệt -> camera chéo
            if dx >= 12 and dy >= 12:
                is_diagonal_camera = True

    # Nhận diện iPhone 13 (2 camera chéo)
    if is_diagonal_camera:
        info = PHONE_MODELS["iphone-13"]
        return {
            "model_id": info["id"],
            "model_name": info["name"],
            "device_code": info["device_code"],
            "case_model_url": info["case_model_url"],
            "confidence": round(max(float(direct_confidence), 0.86), 4)
        }

    # 1. Phân tích vùng camera góc trên trái và góc trên phải (đã lấy từ _detect_camera_bump_candidates)
    scores = {model_id: 0.0 for model_id in PHONE_MODELS}

    # 2. Phân tích chữ 'iPhone' ở đáy lưng máy (chỉ có trên iPhone X / 8)
    bottom_text_region = resized[int(r_h * 0.65):int(r_h * 0.88), int(r_w * 0.20):int(r_w * 0.80)]
    has_iphone_text = False
    if bottom_text_region.size > 0:
        gray_bottom = cv2.cvtColor(bottom_text_region, cv2.COLOR_BGR2GRAY)
        sobel_x = cv2.Sobel(gray_bottom, cv2.CV_64F, 1, 0, ksize=3)
        edge_energy = float(np.mean(np.abs(sobel_x)))
        if edge_energy > 8.0:
            has_iphone_text = True
            scores["iphone-x"] += 0.50

    # 3. Đánh giá cụm camera
    if detected_bump is not None:
        bump_ar = detected_bump["aspect"]
        w_ratio = detected_bump["w_ratio"]

        # A. Cụm hình viên thuốc dọc hẹp (iPhone X)
        if 1.6 <= bump_ar <= 3.2 and w_ratio <= 0.30:
            scores["iphone-x"] += 0.80
            if has_iphone_text:
                scores["iphone-x"] += 0.25

        # B. Cụm camera vuông lớn (iPhone Pro / Pro Max)
        elif 0.75 <= bump_ar <= 1.40 and w_ratio >= 0.32:
            scores["iphone-16-pro-max"] += 0.65
            scores["iphone-15-pro"] += 0.60
            scores["iphone-14-prm"] += 0.55
            scores["iphone-13-prm"] += 0.50
            scores["iphone-12-prm"] += 0.45
            scores["iphone-11-prm"] += 0.40

            if (r_h / float(r_w)) >= 2.08:
                scores["iphone-16-pro-max"] += 0.25

        # C. Cụm camera vuông 2 mắt (iPhone 11, 12, 13)
        elif 0.85 <= bump_ar <= 1.35 and 0.22 <= w_ratio < 0.32:
            scores["iphone-13"] += 0.60
            scores["iphone-12"] += 0.55
            scores["iphone-11"] += 0.50

        # D. Cụm camera chữ nhật 2 tầng dọc đặc trưng (Redmi Note 10 Pro)
        elif 1.45 <= bump_ar <= 2.30 and 0.25 <= w_ratio <= 0.45:
            scores["redmi-note-10-pro"] += 0.85

    if detected_bump is None:
        return None

    # Tìm model có điểm cao nhất
    best_model_id = max(scores, key=scores.get)
    best_score = min(0.98, scores[best_model_id])
    if best_score < 0.30:
        return None

    info = PHONE_MODELS.get(best_model_id, PHONE_MODELS["iphone-15-pro"])
    return {
        "model_id": info["id"],
        "model_name": info["name"],
        "device_code": info["device_code"],
        "case_model_url": info["case_model_url"],
        "confidence": round(best_score, 4)
    }
