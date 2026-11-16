# AI_Service/tools/generate_dataset.py
"""
Script tự động tạo bộ dữ liệu (dataset) chuẩn YOLOv8 để huấn luyện nhận diện
chính xác các dòng iPhone và điện thoại cho tính năng quét camera 3D Try-on Studio.

Các lớp (classes):
0: iphone-x
1: iphone-xr
2: iphone-11
3: iphone-11-prm
4: iphone-12
5: iphone-12-prm
6: iphone-13
7: iphone-13-prm
8: iphone-14-prm
9: iphone-15-pro
10: iphone-16-pro-max
11: iphone-18
12: iphone-18-prm
13: samsung-s24-ultra
14: iphone-15-prm
"""

import os
import math
import random
import numpy as np
import cv2

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

# Màu sắc thực tế của các dòng điện thoại (BGR)
MODEL_COLORS = {
    "iphone-x": [(240, 242, 245), (54, 56, 62), (189, 215, 250)], # Bạc, Xám Space, Gold
    "iphone-xr": [(32, 32, 31), (239, 246, 249), (211, 151, 69), (53, 213, 254), (88, 110, 254), (46, 12, 186)],
    "iphone-11": [(32, 32, 31), (239, 246, 249), (218, 205, 209), (202, 216, 199), (129, 230, 255)],
    "iphone-11-prm": [(81, 88, 78), (70, 74, 76), (227, 235, 235), (189, 215, 250)],
    "iphone-12": [(68, 52, 39), (239, 246, 249), (32, 32, 31), (219, 240, 218), (219, 178, 185)],
    "iphone-12-prm": [(68, 52, 39), (239, 246, 249), (32, 32, 31), (189, 215, 250)],
    "iphone-13": [(50, 35, 26), (242, 246, 250), (215, 221, 250), (125, 94, 33), (56, 76, 57)],
    "iphone-13-prm": [(206, 181, 155), (79, 82, 84), (207, 231, 250), (237, 242, 241)],
    "iphone-14-prm": [(99, 79, 89), (206, 232, 244), (242, 242, 240), (62, 58, 59)],
    "iphone-15-pro": [(180, 196, 208), (66, 53, 45), (62, 59, 60), (225, 228, 226)], # Titan tự nhiên, xanh, đen, trắng
    "iphone-15-prm": [(180, 196, 208), (66, 53, 45), (62, 59, 60), (225, 228, 226)],
    "iphone-16-pro-max": [(152, 176, 197), (180, 196, 208), (225, 228, 226), (62, 59, 60)], # Titan Sa Mạc, Tự nhiên, Trắng, Đen
    "iphone-18": [(62, 59, 60), (180, 196, 208), (225, 228, 226), (10, 16, 98)], # Titan Đen, Tự nhiên, Trắng, Đỏ cherry
    "iphone-18-prm": [(10, 16, 98), (180, 196, 208), (225, 228, 226), (62, 59, 60)], # Đỏ cherry, Tự nhiên, Trắng, Đen
    "samsung-s24-ultra": [(124, 128, 130), (38, 38, 38), (80, 60, 72), (200, 230, 245)]
}

def create_background(w, h):
    """Tạo các hình nền tự nhiên như mặt bàn gỗ, đá marble, bàn làm việc, ánh sáng phòng."""
    bg_type = random.choice(["wood", "desk", "marble", "ambient", "gradient"])
    bg = np.zeros((h, w, 3), dtype=np.uint8)

    if bg_type == "wood":
        base_color = np.array([random.randint(25, 60), random.randint(50, 95), random.randint(90, 150)], dtype=np.float32)
        bg[:] = base_color
        noise = np.random.normal(0, 8, (h, w, 3))
        bg = np.clip(bg + noise, 0, 255).astype(np.uint8)
        # Vân gỗ nhẹ
        for y in range(0, h, random.randint(15, 30)):
            cv2.line(bg, (0, y), (w, y + random.randint(-5, 5)), (int(base_color[0]*0.85), int(base_color[1]*0.85), int(base_color[2]*0.85)), 1)
    elif bg_type == "marble":
        val = random.randint(190, 235)
        bg[:] = [val, val, val]
        noise = np.random.normal(0, 12, (h, w, 3))
        bg = np.clip(bg + noise, 0, 255).astype(np.uint8)
    elif bg_type == "desk":
        val = random.randint(40, 90)
        bg[:] = [val, val, val]
        noise = np.random.normal(0, 10, (h, w, 3))
        bg = np.clip(bg + noise, 0, 255).astype(np.uint8)
    elif bg_type == "gradient":
        c1 = [random.randint(30, 120) for _ in range(3)]
        c2 = [random.randint(40, 150) for _ in range(3)]
        for y in range(h):
            alpha = y / float(h)
            color = [int(c1[i] * (1 - alpha) + c2[i] * alpha) for i in range(3)]
            bg[y, :] = color
    else:
        val = random.randint(60, 140)
        bg[:] = [val, val, val]

    # Hiệu ứng vignette góc tối tự nhiên
    Y, X = np.ogrid[:h, :w]
    center_y, center_x = h / 2.0, w / 2.0
    dist_from_center = np.sqrt((X - center_x)**2 + (Y - center_y)**2)
    max_dist = np.sqrt(center_x**2 + center_y**2)
    vignette = 1.0 - 0.35 * (dist_from_center / max_dist)
    bg = np.clip(bg * vignette[:, :, np.newaxis], 0, 255).astype(np.uint8)
    return bg

def draw_rounded_rect(img, pt1, pt2, color, radius, thickness=-1):
    """Vẽ hình chữ nhật bo góc mượt mà."""
    x1, y1 = pt1
    x2, y2 = pt2
    r = min(radius, abs(x2 - x1) // 2, abs(y2 - y1) // 2)
    if r <= 0:
        cv2.rectangle(img, pt1, pt2, color, thickness)
        return

    # Phần giữa
    cv2.rectangle(img, (x1 + r, y1), (x2 - r, y2), color, thickness)
    cv2.rectangle(img, (x1, y1 + r), (x2, y2 - r), color, thickness)
    # 4 góc
    cv2.circle(img, (x1 + r, y1 + r), r, color, thickness)
    cv2.circle(img, (x2 - r, y1 + r), r, color, thickness)
    cv2.circle(img, (x1 + r, y2 - r), r, color, thickness)
    cv2.circle(img, (x2 - r, y2 - r), r, color, thickness)

def draw_camera_module(phone_layer, model_name, pw, ph, body_color):
    """
    Vẽ cụm camera đặc trưng riêng của từng dòng điện thoại.
    Đây là yếu tố then chốt giúp mô hình YOLO phân biệt 100% chính xác từng dòng máy.
    """
    # Màu kính cụm camera (thường tối hoặc cùng màu máy)
    is_matte = "prm" in model_name or "pro" in model_name
    bump_color = tuple(int(c * 0.92) if is_matte else int(c * 1.08) for c in body_color)
    bump_color = tuple(max(15, min(240, c)) for c in bump_color)

    # 1. IPHONE X / XS: Cụm viên thuốc dọc hẹp, 2 mắt camera dọc, đèn flash ở giữa
    if model_name == "iphone-x":
        bw = int(pw * 0.22)
        bh = int(ph * 0.22)
        bx = int(pw * 0.08)
        by = int(ph * 0.06)
        # Kính bảo vệ hình viên thuốc (pill)
        draw_rounded_rect(phone_layer, (bx, by), (bx + bw, by + bh), (20, 20, 22), bw // 2)
        # Viền kim loại bóng
        cv2.ellipse(phone_layer, (bx + bw//2, by + bw//2), (bw//2, bw//2), 0, 180, 360, (200, 200, 205), 1)
        # Camera trên
        c1_y = by + int(bh * 0.24)
        cv2.circle(phone_layer, (bx + bw // 2, c1_y), int(bw * 0.36), (10, 10, 12), -1)
        cv2.circle(phone_layer, (bx + bw // 2, c1_y), int(bw * 0.16), (40, 50, 70), -1) # Kính phản xạ
        # Flash ở giữa
        flash_y = by + int(bh * 0.50)
        cv2.circle(phone_layer, (bx + bw // 2, flash_y), int(bw * 0.16), (220, 240, 255), -1)
        # Camera dưới
        c2_y = by + int(bh * 0.76)
        cv2.circle(phone_layer, (bx + bw // 2, c2_y), int(bw * 0.36), (10, 10, 12), -1)
        cv2.circle(phone_layer, (bx + bw // 2, c2_y), int(bw * 0.16), (40, 50, 70), -1)

        # Dòng chữ "iPhone" ở đáy lưng chỉ có ở iPhone X / 8 trở về trước
        text_y = int(ph * 0.82)
        cv2.putText(phone_layer, "iPhone", (int(pw * 0.38), text_y), cv2.FONT_HERSHEY_SIMPLEX, pw * 0.0016, (140, 140, 145), 1, cv2.LINE_AA)

    # 2. IPHONE XR: 1 mắt camera tròn duy nhất, flash bên dưới
    elif model_name == "iphone-xr":
        cx = int(pw * 0.18)
        cy = int(ph * 0.11)
        cr = int(pw * 0.11)
        cv2.circle(phone_layer, (cx, cy), cr + 2, (200, 200, 200), 2)
        cv2.circle(phone_layer, (cx, cy), cr, (15, 15, 18), -1)
        cv2.circle(phone_layer, (cx, cy), int(cr * 0.45), (45, 55, 75), -1)
        # Flash tròn dưới
        cv2.circle(phone_layer, (cx, cy + int(cr * 2.2)), int(cr * 0.38), (220, 240, 255), -1)

    # 3. IPHONE 11: Cụm vuông bo góc, 2 mắt camera dọc, flash bên phải
    elif model_name == "iphone-11":
        bw = int(pw * 0.36)
        bh = int(pw * 0.36)
        bx = int(pw * 0.07)
        by = int(ph * 0.045)
        draw_rounded_rect(phone_layer, (bx, by), (bx + bw, by + bh), bump_color, int(bw * 0.28))
        lens_r = int(bw * 0.22)
        lx = bx + int(bw * 0.32)
        # 2 mắt camera xếp thẳng đứng
        for ly in [by + int(bh * 0.28), by + int(bh * 0.72)]:
            cv2.circle(phone_layer, (lx, ly), lens_r + 1, (180, 180, 185), 1)
            cv2.circle(phone_layer, (lx, ly), lens_r, (12, 12, 15), -1)
            cv2.circle(phone_layer, (lx, ly), int(lens_r * 0.42), (40, 55, 80), -1)
        # Flash ở bên phải
        cv2.circle(phone_layer, (bx + int(bw * 0.75), by + int(bh * 0.50)), int(lens_r * 0.35), (230, 245, 255), -1)

    # 4. IPHONE 12: Viền phẳng, cụm vuông 2 mắt camera chéo
    elif model_name == "iphone-12":
        bw = int(pw * 0.38)
        bh = int(pw * 0.38)
        bx = int(pw * 0.07)
        by = int(ph * 0.045)
        draw_rounded_rect(phone_layer, (bx, by), (bx + bw, by + bh), bump_color, int(bw * 0.26))
        lens_r = int(bw * 0.23)
        for center in [
            (bx + int(bw * 0.32), by + int(bh * 0.32)),
            (bx + int(bw * 0.68), by + int(bh * 0.68))
        ]:
            cv2.circle(phone_layer, center, lens_r + 2, (190, 190, 195), 1)
            cv2.circle(phone_layer, center, lens_r, (12, 12, 15), -1)
            cv2.circle(phone_layer, center, int(lens_r * 0.42), (40, 55, 80), -1)
        cv2.circle(phone_layer, (bx + int(bw * 0.75), by + int(bh * 0.50)), int(lens_r * 0.35), (230, 245, 255), -1)

    # 5. IPHONE 13: Cụm vuông, 2 MẮT CAMERA XẾP CHÉO ĐẶC TRƯNG (Top-left & Bottom-right)
    elif model_name == "iphone-13":
        bw = int(pw * 0.40)
        bh = int(pw * 0.40)
        bx = int(pw * 0.07)
        by = int(ph * 0.045)
        draw_rounded_rect(phone_layer, (bx, by), (bx + bw, by + bh), bump_color, int(bw * 0.26))
        lens_r = int(bw * 0.23)
        # Ống kính 1: góc trên trái
        c1 = (bx + int(bw * 0.32), by + int(bh * 0.32))
        cv2.circle(phone_layer, c1, lens_r + 2, (190, 190, 195), 1)
        cv2.circle(phone_layer, c1, lens_r, (12, 12, 15), -1)
        cv2.circle(phone_layer, c1, int(lens_r * 0.42), (40, 55, 80), -1)
        # Ống kính 2: góc dưới phải
        c2 = (bx + int(bw * 0.68), by + int(bh * 0.68))
        cv2.circle(phone_layer, c2, lens_r + 2, (190, 190, 195), 1)
        cv2.circle(phone_layer, c2, lens_r, (12, 12, 15), -1)
        cv2.circle(phone_layer, c2, int(lens_r * 0.42), (40, 55, 80), -1)
        # Đèn flash góc trên phải
        cv2.circle(phone_layer, (bx + int(bw * 0.70), by + int(bh * 0.28)), int(lens_r * 0.36), (230, 245, 255), -1)

    # 5b. IPHONE 18: Cụm camera kép chéo theo model GLB mới
    elif model_name == "iphone-18":
        bw = int(pw * 0.40)
        bh = int(pw * 0.40)
        bx = int(pw * 0.08)
        by = int(ph * 0.05)
        draw_rounded_rect(phone_layer, (bx, by), (bx + bw, by + bh), bump_color, int(bw * 0.28))
        lens_r = int(bw * 0.22)
        for center in [
            (bx + int(bw * 0.32), by + int(bh * 0.32)),
            (bx + int(bw * 0.68), by + int(bh * 0.68))
        ]:
            cv2.circle(phone_layer, center, lens_r + 2, (190, 190, 195), 2)
            cv2.circle(phone_layer, center, lens_r, (12, 12, 15), -1)
            cv2.circle(phone_layer, center, int(lens_r * 0.42), (40, 55, 80), -1)
        cv2.circle(phone_layer, (bx + int(bw * 0.72), by + int(bh * 0.34)), int(lens_r * 0.34), (230, 245, 255), -1)

    # 6. CÁC DÒNG IPHONE PRO / PRO MAX: Cụm 3 mắt tam giác (11 PRM, 12 PRM, 13 PRM, 14 PRM, 15 Pro, 16 Pro Max, 18 PRM)
    elif any(tag in model_name for tag in ["prm", "pro"]):
        # Kích thước cụm camera to dần theo các thế hệ
        bump_ratio = 0.40 if "11" in model_name else (0.43 if "12" in model_name else (0.47 if "13" in model_name else (0.54 if any(v in model_name for v in ["16", "18"]) else 0.50)))
        bw = int(pw * bump_ratio)
        bh = int(pw * bump_ratio)
        bx = int(pw * 0.06)
        by = int(ph * 0.04)
        draw_rounded_rect(phone_layer, (bx, by), (bx + bw, by + bh), bump_color, int(bw * 0.28))

        lens_ratio = 0.21 if "11" in model_name else (0.23 if "12" in model_name else 0.25)
        lens_r = int(bw * lens_ratio)

        # 3 mắt xếp theo tam giác chuẩn Apple
        l1 = (bx + int(bw * 0.32), by + int(bh * 0.28)) # Trên trái
        l2 = (bx + int(bw * 0.32), by + int(bh * 0.72)) # Dưới trái
        l3 = (bx + int(bw * 0.68), by + int(bh * 0.50)) # Giữa phải

        ring_color = (190, 195, 200) if "titan" not in model_name else (160, 175, 185)
        for pt in [l1, l2, l3]:
            cv2.circle(phone_layer, pt, lens_r + 2, ring_color, 2)
            cv2.circle(phone_layer, pt, lens_r, (10, 10, 12), -1)
            cv2.circle(phone_layer, pt, int(lens_r * 0.45), (35, 50, 75), -1)

        # Đèn Flash (Góc trên phải)
        flash_pt = (bx + int(bw * 0.70), by + int(bh * 0.22))
        cv2.circle(phone_layer, flash_pt, int(lens_r * 0.36), (230, 245, 255), -1)

        # Mắt cảm biến LiDAR tròn đen đặc trưng (12 Pro trở lên)
        if "11" not in model_name:
            lidar_pt = (bx + int(bw * 0.70), by + int(bh * 0.78))
            cv2.circle(phone_layer, lidar_pt, int(lens_r * 0.30), (15, 15, 18), -1)

        # Nút Action Button & Camera Control đặc trưng của iPhone 16 / 18 Pro Max ở cạnh sườn
        if any(v in model_name for v in ["16", "18"]):
            btn_y = int(ph * 0.65)
            cv2.line(phone_layer, (pw - 2, btn_y), (pw - 2, btn_y + int(ph * 0.08)), (190, 175, 150), 2)

    # 7. SAMSUNG S24 ULTRA: Thiết kế vuông góc, các vòng camera rời độc lập thẳng hàng
    elif model_name == "samsung-s24-ultra":
        cx = int(pw * 0.16)
        r_main = int(pw * 0.09)
        # 3 ống kính lớn xếp thẳng đứng bên trái
        y_positions = [int(ph * 0.08), int(ph * 0.17), int(ph * 0.26)]
        for y in y_positions:
            cv2.circle(phone_layer, (cx, y), r_main + 2, (170, 170, 175), 2)
            cv2.circle(phone_layer, (cx, y), r_main, (10, 10, 12), -1)
            cv2.circle(phone_layer, (cx, y), int(r_main * 0.42), (40, 50, 70), -1)
        # 2 mắt phụ & đèn flash ở cột bên phải
        cx2 = cx + int(pw * 0.15)
        cv2.circle(phone_layer, (cx2, int(ph * 0.09)), int(r_main * 0.5), (230, 245, 255), -1) # Flash
        cv2.circle(phone_layer, (cx2, int(ph * 0.16)), int(r_main * 0.7), (10, 10, 12), -1)
        cv2.circle(phone_layer, (cx2, int(ph * 0.24)), int(r_main * 0.7), (10, 10, 12), -1)

    # Vẽ Logo Apple ở trung tâm lưng máy (Cho tất cả iPhone)
    if "iphone" in model_name:
        logo_y = int(ph * 0.50) if model_name != "iphone-x" else int(ph * 0.44)
        logo_x = int(pw * 0.50)
        logo_r = int(pw * 0.045)
        logo_color = tuple(max(10, min(245, int(c * 1.15))) for c in body_color)
        cv2.circle(phone_layer, (logo_x, logo_y), logo_r, logo_color, -1)
        # Vết khuyết bên phải logo Apple
        cv2.circle(phone_layer, (logo_x + int(logo_r * 0.7), logo_y), int(logo_r * 0.45), body_color, -1)

def generate_synthetic_phone_sample(model_name, img_w=640, img_h=640):
    """
    Tạo 1 ảnh tổng hợp chân thực có góc nghiêng, ánh sáng, phối cảnh và trả về
    ảnh RGB cùng nhãn bounding box chuẩn YOLO [cls, x_c, y_c, w, h].
    """
    bg = create_background(img_w, img_h)

    # Kích thước điện thoại (pixel)
    scale = random.uniform(0.55, 0.85)
    pw = int(img_w * 0.42 * scale)
    aspect_ratio = random.uniform(2.05, 2.18) if "ultra" in model_name or "16" in model_name else random.uniform(1.95, 2.10)
    ph = int(pw * aspect_ratio)

    phone_layer = np.zeros((ph, pw, 4), dtype=np.uint8) # RGBA

    # Chọn màu ngẫu nhiên cho dòng máy
    color_palette = MODEL_COLORS.get(model_name, [(50, 50, 50)])
    base_color = random.choice(color_palette)

    # Thân máy
    corner_radius = 2 if model_name == "samsung-s24-ultra" else int(pw * 0.12)
    temp_body = np.zeros((ph, pw, 3), dtype=np.uint8)
    draw_rounded_rect(temp_body, (0, 0), (pw, ph), base_color, corner_radius)

    # Viền kim loại / titanium
    frame_color = tuple(min(255, int(c * 1.25) + 20) for c in base_color)
    cv2.rectangle(temp_body, (0, 0), (pw, ph), frame_color, 2)

    # Cụm camera đặc trưng
    draw_camera_module(temp_body, model_name, pw, ph, base_color)

    # Alpha mask cho thân máy
    mask = np.zeros((ph, pw), dtype=np.uint8)
    draw_rounded_rect(mask, (0, 0), (pw, ph), 255, corner_radius)

    phone_rgba = cv2.cvtColor(temp_body, cv2.COLOR_BGR2BGRA)
    phone_rgba[:, :, 3] = mask

    # Phép biến đổi: Xoay ngẫu nhiên từ -25 đến +25 độ
    angle = random.uniform(-25.0, 25.0)
    rot_mat = cv2.getRotationMatrix2D((pw / 2.0, ph / 2.0), angle, 1.0)
    cos = np.abs(rot_mat[0, 0])
    sin = np.abs(rot_mat[0, 1])
    bound_w = int((ph * sin) + (pw * cos))
    bound_h = int((ph * cos) + (pw * sin))
    rot_mat[0, 2] += (bound_w / 2) - pw / 2
    rot_mat[1, 2] += (bound_h / 2) - ph / 2

    rotated_phone = cv2.warpAffine(phone_rgba, rot_mat, (bound_w, bound_h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0,0,0,0))

    # Tọa độ dán lên background
    max_x = max(10, img_w - bound_w - 10)
    max_y = max(10, img_h - bound_h - 10)
    pos_x = random.randint(10, max_x)
    pos_y = random.randint(10, max_y)

    # Đổ bóng (drop shadow) mềm dưới điện thoại
    shadow_mask = cv2.dilate(rotated_phone[:, :, 3], np.ones((9, 9), np.uint8), iterations=2)
    shadow_mask = cv2.GaussianBlur(shadow_mask, (21, 21), 0)
    s_offset_x = pos_x + random.randint(6, 14)
    s_offset_y = pos_y + random.randint(8, 18)

    # Dán shadow lên bg
    sh_h, sh_w = shadow_mask.shape
    if 0 <= s_offset_y < img_h and 0 <= s_offset_x < img_w:
        sh_clip_h = min(sh_h, img_h - s_offset_y)
        sh_clip_w = min(sh_w, img_w - s_offset_x)
        bg_roi = bg[s_offset_y:s_offset_y+sh_clip_h, s_offset_x:s_offset_x+sh_clip_w]
        sh_alpha = (shadow_mask[:sh_clip_h, :sh_clip_w] / 255.0) * 0.45
        for c in range(3):
            bg_roi[:, :, c] = (bg_roi[:, :, c] * (1.0 - sh_alpha)).astype(np.uint8)

    # Dán điện thoại lên background
    clip_h = min(bound_h, img_h - pos_y)
    clip_w = min(bound_w, img_w - pos_x)
    alpha = rotated_phone[:clip_h, :clip_w, 3] / 255.0
    for c in range(3):
        bg[pos_y:pos_y+clip_h, pos_x:pos_x+clip_w, c] = (
            bg[pos_y:pos_y+clip_h, pos_x:pos_x+clip_w, c] * (1.0 - alpha) +
            rotated_phone[:clip_h, :clip_w, c] * alpha
        ).astype(np.uint8)

    # Tính Bounding Box chuẩn xác dựa vào alpha mask
    ys, xs = np.where(rotated_phone[:, :, 3] > 10)
    if len(xs) > 0 and len(ys) > 0:
        bx1 = np.min(xs) + pos_x
        bx2 = np.max(xs) + pos_x
        by1 = np.min(ys) + pos_y
        by2 = np.max(ys) + pos_y

        bx1 = max(0, min(img_w - 1, bx1))
        bx2 = max(0, min(img_w - 1, bx2))
        by1 = max(0, min(img_h - 1, by1))
        by2 = max(0, min(img_h - 1, by2))

        # Chuyển đổi sang format YOLO [x_center, y_center, width, height] chuẩn hóa (0.0 - 1.0)
        bw_box = bx2 - bx1
        bh_box = by2 - by1
        xc = (bx1 + bw_box / 2.0) / float(img_w)
        yc = (by1 + bh_box / 2.0) / float(img_h)
        nw = bw_box / float(img_w)
        nh = bh_box / float(img_h)

        cls_id = CLASS_TO_ID[model_name]
        return bg, [cls_id, xc, yc, nw, nh]

    return bg, None

def build_yolo_dataset(output_dir, samples_per_class=40, val_ratio=0.2):
    """
    Sinh toàn bộ tập dữ liệu huấn luyện và kiểm định chuẩn YOLO.
    """
    images_train = os.path.join(output_dir, "images", "train")
    images_val = os.path.join(output_dir, "images", "val")
    labels_train = os.path.join(output_dir, "labels", "train")
    labels_val = os.path.join(output_dir, "labels", "val")

    for p in [images_train, images_val, labels_train, labels_val]:
        os.makedirs(p, exist_ok=True)

    print(f"Bắt đầu sinh dataset YOLO cho {len(CLASSES)} dòng điện thoại...")
    total_samples = 0

    for cls_name in CLASSES:
        print(f" -> Đang tạo dữ liệu cho: {cls_name} ({samples_per_class} mẫu)")
        val_count = min(max(round(samples_per_class * val_ratio), 1), samples_per_class - 1)
        val_indices = set(random.sample(range(samples_per_class), val_count))
        for i in range(samples_per_class):
            img, bbox = generate_synthetic_phone_sample(cls_name, 640, 640)
            if bbox is None:
                continue

            is_val = i in val_indices
            target_img_dir = images_val if is_val else images_train
            target_lbl_dir = labels_val if is_val else labels_train

            filename = f"{cls_name}_{i:04d}"
            img_path = os.path.join(target_img_dir, f"{filename}.jpg")
            lbl_path = os.path.join(target_lbl_dir, f"{filename}.txt")

            cv2.imwrite(img_path, img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
            with open(lbl_path, "w", encoding="utf-8") as f:
                f.write(f"{bbox[0]} {bbox[1]:.6f} {bbox[2]:.6f} {bbox[3]:.6f} {bbox[4]:.6f}\n")

            total_samples += 1

    # TỰ ĐỘNG NẠP VÀ AUGMENT ẢNH THẬT NẾU NGƯỜI DÙNG BỎ ẢNH VÀO raw_images/<class_name>/
    raw_images_dir = os.path.join(output_dir, "raw_images")
    if os.path.exists(raw_images_dir):
        for cls_name in CLASSES:
            cls_raw_dir = os.path.join(raw_images_dir, cls_name)
            if not os.path.isdir(cls_raw_dir):
                os.makedirs(cls_raw_dir, exist_ok=True)
                continue

            raw_files = [f for f in os.listdir(cls_raw_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            if not raw_files:
                continue

            print(f" -> Đã nạp {len(raw_files)} ảnh chụp thực tế cho [{cls_name}]")
            cls_id = CLASS_TO_ID[cls_name]
            for idx, rfile in enumerate(raw_files):
                rpath = os.path.join(cls_raw_dir, rfile)
                rimg = cv2.imread(rpath)
                if rimg is None:
                    continue

                rh, rw = rimg.shape[:2]
                target_size = 640
                scale_f = target_size / max(rh, rw)
                nw, nh = int(rw * scale_f), int(rh * scale_f)
                resized = cv2.resize(rimg, (nw, nh), interpolation=cv2.INTER_AREA)

                canvas = np.zeros((target_size, target_size, 3), dtype=np.uint8)
                dx = (target_size - nw) // 2
                dy = (target_size - nh) // 2
                canvas[dy:dy+nh, dx:dx+nw] = resized

                xc = 0.5
                yc = 0.5
                box_w = (nw * 0.92) / float(target_size)
                box_h = (nh * 0.92) / float(target_size)

                is_val = (random.random() < val_ratio)
                target_img_dir = images_val if is_val else images_train
                target_lbl_dir = labels_val if is_val else labels_train

                out_name = f"real_{cls_name}_{idx:04d}"
                cv2.imwrite(os.path.join(target_img_dir, f"{out_name}.jpg"), canvas, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
                with open(os.path.join(target_lbl_dir, f"{out_name}.txt"), "w", encoding="utf-8") as f:
                    f.write(f"{cls_id} {xc:.6f} {yc:.6f} {box_w:.6f} {box_h:.6f}\n")
                total_samples += 1

    # Tạo file data.yaml không phụ thuộc thư viện bên ngoài
    yaml_path = os.path.join(output_dir, "data.yaml")
    clean_path = os.path.abspath(output_dir).replace("\\", "/")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(f"path: {clean_path}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write("names:\n")
        for idx, name in enumerate(CLASSES):
            f.write(f"  {idx}: {name}\n")

    print(f"\n Hoàn tất sinh {total_samples} ảnh mẫu.")
    print(f" File cấu hình YOLO: {yaml_path}")
    return yaml_path

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_path = os.path.join(base_dir, "dataset")
    build_yolo_dataset(dataset_path, samples_per_class=35)
