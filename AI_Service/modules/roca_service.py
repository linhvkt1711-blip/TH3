# AI_Service/modules/roca_service.py
try:
    import torch  # type: ignore
    import torch.nn as nn  # type: ignore
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import numpy as np  # type: ignore
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import cv2  # type: ignore
    from PIL import Image  # type: ignore
    import torchvision.models as models  # type: ignore
    import torchvision.transforms as transforms  # type: ignore
except ImportError:
    pass

from .roca_procrustes import ROCAAlignmentHead

class PhonePoseEstimationPipeline:
    def __init__(self, device="cuda" if HAS_TORCH and torch.cuda.is_available() else "cpu"):
        self.device = device

        # ROCA Head
        if HAS_TORCH:
            self.roca_head = ROCAAlignmentHead().to(self.device)
            self.roca_head.eval()
        else:
            # Sửa tỷ lệ scale mặc định thành của iPhone 16 Pro Max
            pred_scale = [0.0776, 0.1630, 0.00825] 
            R_star = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
            t_star = [0.0, 0.0, 0.35]
        # Database kích thước chuẩn CAD của các dòng máy (Dài x Rộng x Dày tính bằng mét)
        # Database kích thước chuẩn CAD của các dòng máy (Dài x Rộng x Dày tính bằng mét)
        if HAS_NUMPY:
            self.cad_database = {
                "iphone-x": np.array([0.0709, 0.1436, 0.0077]),
                "iphone-xr": np.array([0.0757, 0.1509, 0.0083]),
                "iphone-11": np.array([0.0757, 0.1509, 0.0083]),
                "iphone-11-prm": np.array([0.0778, 0.1580, 0.0081]),
                "iphone-12": np.array([0.0715, 0.1467, 0.0074]),
                "iphone-12-prm": np.array([0.0781, 0.1608, 0.0074]),
                "iphone-13": np.array([0.0715, 0.1467, 0.00765]),
                "iphone-13-prm": np.array([0.0781, 0.1608, 0.00765]),
                "iphone-14-prm": np.array([0.0776, 0.1607, 0.00785]),
                "iphone-15-pro": np.array([0.0706, 0.1466, 0.00825]),
                "iphone-15-prm": np.array([0.0767, 0.1599, 0.00825]),
                "iphone-16-pro-max": np.array([0.0776, 0.1630, 0.00825]),
                "iphone-18": np.array([0.0716, 0.1476, 0.0078]),
                "iphone-18-prm": np.array([0.0776, 0.1630, 0.00825]),
                "samsung-s24-ultra": np.array([0.0790, 0.1623, 0.00860])
            }
        else:
            self.cad_database = {
                "iphone-x": [0.0709, 0.1436, 0.0077],
                "iphone-xr": [0.0757, 0.1509, 0.0083],
                "iphone-11": [0.0757, 0.1509, 0.0083],
                "iphone-11-prm": [0.0778, 0.1580, 0.0081],
                "iphone-12": [0.0715, 0.1467, 0.0074],
                "iphone-12-prm": [0.0781, 0.1608, 0.0074],
                "iphone-13": [0.0715, 0.1467, 0.00765],
                "iphone-13-prm": [0.0781, 0.1608, 0.00765],
                "iphone-14-prm": [0.0776, 0.1607, 0.00785],
                "iphone-15-pro": [0.0706, 0.1466, 0.00825],
                "iphone-15-prm": [0.0767, 0.1599, 0.00825],
                "iphone-16-pro-max": [0.0776, 0.1630, 0.00825],
                "iphone-18": [0.0716, 0.1476, 0.0078],
                "iphone-18-prm": [0.0776, 0.1630, 0.00825],
                "samsung-s24-ultra": [0.0790, 0.1623, 0.00860]
            }

    def infer(self, cropped_bgr_image, matched_model_id=None):
        """
        Nhận ảnh crop từ Bounding Box của YOLO, ước lượng tư thế 6DoF
        và truy vấn mã dòng máy CAD khớp nhất.
        """
        h, w = 480, 640
        if hasattr(cropped_bgr_image, "shape"):
            h, w = cropped_bgr_image.shape[:2]

        aspect_ratio = h / float(w) if w > 0 else 2.0

        if matched_model_id in self.cad_database:
            matched_cad_id = matched_model_id
        elif aspect_ratio > 2.08:
            matched_cad_id = "samsung-s24-ultra"
        elif aspect_ratio > 1.98:
            matched_cad_id = "iphone-16-pro-max"
        else:
            matched_cad_id = "iphone-16-pro-max"

        # The ROCA head has no trained checkpoint, so use a stable neutral pose.
        pred_scale = self.cad_database[matched_cad_id]
        if HAS_NUMPY:
            pred_scale = pred_scale.tolist()
        else:
            pred_scale = list(pred_scale)

        R_star = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        t_star = [0.0, 0.0, 0.35]

        return {
            "matched_cad_id": matched_cad_id,
            "predicted_scale": pred_scale,
            "rotation_matrix": R_star,
            "translation_vector": t_star
        }
