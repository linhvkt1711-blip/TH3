# AI_Service/app.py
import os
import re
import sys

# Đảm bảo đường dẫn tìm kiếm module bao gồm cả thư mục AI_Service
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
    from fastapi import FastAPI, UploadFile, File, Form, Request  # type: ignore
    from fastapi.responses import JSONResponse  # type: ignore
    from fastapi.middleware.cors import CORSMiddleware  # type: ignore
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

try:
    from modules.recommender import get_hybrid_recommendations  # type: ignore
except ImportError:
    try:
        from AI_Service.modules.recommender import get_hybrid_recommendations  # type: ignore
    except ImportError:
        get_hybrid_recommendations = None

try:
    from modules.roca_service import PhonePoseEstimationPipeline  # type: ignore
except ImportError:
    try:
        from AI_Service.modules.roca_service import PhonePoseEstimationPipeline  # type: ignore
    except ImportError:
        PhonePoseEstimationPipeline = None

try:
    from modules.phone_classifier import detect_phone_bbox, classify_phone, PHONE_MODELS  # type: ignore
except ImportError:
    try:
        from AI_Service.modules.phone_classifier import detect_phone_bbox, classify_phone, PHONE_MODELS  # type: ignore
    except ImportError:
        detect_phone_bbox = None
        classify_phone = None
        PHONE_MODELS = {}

if HAS_FASTAPI:
    app = FastAPI(title="AI Phone Detection & ROCA 6DoF Alignment API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app = None

# Khởi tạo ROCA pipeline
roca_pipeline = PhonePoseEstimationPipeline() if PhonePoseEstimationPipeline else None

# Tải YOLO nếu có ultralytics
yolo_model = None
YOLO_ERROR = None
try:
    os.environ["YOLO_CONFIG_DIR"] = os.path.join(current_dir, ".config")
    from ultralytics import YOLO  # type: ignore
    configured_weights = os.environ.get("PHONE_YOLO_WEIGHTS")
    if configured_weights:
        weights_path = (
            configured_weights
            if os.path.isabs(configured_weights)
            else os.path.join(current_dir, configured_weights)
        )
        if not os.path.isfile(weights_path):
            raise FileNotFoundError(f"YOLO weights not found: {weights_path}")
        yolo_model = YOLO(weights_path)
    else:
        weights_path = os.path.join(current_dir, "weights", "yolo_phone_detect.pt")
        if os.path.exists(weights_path):
            yolo_model = YOLO(weights_path)
        elif os.path.exists(os.path.join(current_dir, "weights", "yolov8n.pt")):
            yolo_model = YOLO(os.path.join(current_dir, "weights", "yolov8n.pt"))
        else:
            yolo_model = YOLO("yolov8n.pt")
except Exception as error:
    YOLO_ERROR = str(error)
    print(f"Không tải được model YOLO: {YOLO_ERROR}", file=sys.stderr)

PHONE_NAMES = {
    "iphone-x": "iPhone X / Xs (iPhone 10)",
    "iphone-11": "iPhone 11",
    "iphone-11-prm": "iPhone 11 Pro Max",
    "iphone-12": "iPhone 12",
    "iphone-12-prm": "iPhone 12 Pro Max",
    "iphone-13": "iPhone 13",
    "iphone-13-prm": "iPhone 13 Pro Max",
    "iphone-14-prm": "iPhone 14 Pro Max",
    "iphone-15-pro": "iPhone 15 Pro",
    "iphone-16-pro-max": "iPhone 16 Pro Max",
    "iphone-17-prm": "iPhone 17 Pro Max",
    "iphone-18-prm": "iPhone 18 Pro Max",
    "redmi-note-10-pro": "Xiaomi Redmi Note 10 Pro"
}

PHONE_DEVICE_CODES = {
    "iphone-x": "IPX01",
    "iphone-11": "IP11",
    "iphone-11-prm": "IP11PM",
    "iphone-12": "IP12",
    "iphone-12-prm": "IP12PM",
    "iphone-13": "IP13",
    "iphone-13-prm": "IP13PM",
    "iphone-14-prm": "IP14PM",
    "iphone-15-pro": "IP01",
    "iphone-16-pro-max": "IP05",
    "iphone-17-prm": "IP17PM",
    "iphone-18-prm": "IP18PM",
    "redmi-note-10-pro": "RMN10P",
}

if app is not None:
    @app.get("/")
    def health_check():
        return {
            "status": "ok" if (yolo_model is not None or classify_phone is not None) else "unavailable",
            "service": "AI Phone Case Try-on YOLO + ROCA Inference API",
            "yolo_ready": yolo_model is not None,
            "yolo_error": YOLO_ERROR,
            "recommendation_ready": get_hybrid_recommendations is not None
        }

    @app.post("/recommend")
    @app.post("/api/recommend")
    async def recommend_products(request: Request):
        """API gợi ý ốp lưng: Hybrid 60% Implicit + 40% Explicit Preferences."""
        try:
            payload = await request.json()
        except Exception:
            payload = {}

        user_data            = payload.get("user") or {}
        products             = payload.get("products") or []
        history              = payload.get("history") or []
        target_device_code   = payload.get("target_device_code") or user_data.get("device_code")
        explicit_preferences = payload.get("explicit_preferences") or None

        if get_hybrid_recommendations is not None:
            res = get_hybrid_recommendations(
                user_data=user_data,
                products=products,
                history=history,
                target_device_code=target_device_code,
                top_k=5,
                explicit_preferences=explicit_preferences
            )
            return res.get("recommendations", [])

        # Fallback cơ bản nếu module gợi ý chưa tải
        return products[:5]

    @app.post("/api/recommend-details")
    async def recommend_products_details(request: Request):
        """API gợi ý chi tiết bao gồm danh sách đề xuất và bộ chỉ số (Precision@5, Recall@5, NDCG@5)."""
        try:
            payload = await request.json()
        except Exception:
            payload = {}

        user_data            = payload.get("user") or {}
        products             = payload.get("products") or []
        history              = payload.get("history") or []
        target_device_code   = payload.get("target_device_code") or user_data.get("device_code")
        explicit_preferences = payload.get("explicit_preferences") or None

        if get_hybrid_recommendations is not None:
            return get_hybrid_recommendations(
                user_data=user_data,
                products=products,
                history=history,
                target_device_code=target_device_code,
                top_k=5,
                explicit_preferences=explicit_preferences
            )
        return {"success": False, "message": "Recommendation engine not available"}

    @app.post("/api/detect-phone-model")
    async def detect_phone_model(file: UploadFile = File(...), source: str = Form("camera")):
        source = "upload" if source.strip().lower() == "upload" else "camera"
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return {"success": False, "message": "File ảnh không hợp lệ."}

        h, w, _ = image.shape

        # 1. Phát hiện Bounding Box và dòng máy qua YOLO hoặc Fallback
        direct_model_id = None
        if detect_phone_bbox is not None:
            bbox, confidence, direct_model_id = detect_phone_bbox(image, yolo_model)
        else:
            return {
                "success": False,
                "phone_detected": False,
                "model_recognized": False,
                "message": "Bộ nhận diện điện thoại chưa được tải. Hãy kiểm tra AI Service."
            }

        if bbox is None:
            message = (
                "Không nhận diện được điện thoại trong ảnh đã tải lên. Hãy chọn ảnh chỉ có một điện thoại, "
                "thấy rõ mặt lưng và cụm camera; ảnh ghép mặt trước/mặt sau có thể khó nhận diện. "
                "Bạn cũng có thể chọn model 3D thủ công."
                if source == "upload"
                else "Không phát hiện điện thoại trong khung camera. Hãy đưa rõ mặt lưng và cụm camera vào khung hình rồi thử lại."
            )
            return {
                "success": False,
                "phone_detected": False,
                "model_recognized": False,
                "message": message
            }

        # 2. Phân loại chi tiết và ánh xạ model 3D
        if classify_phone is not None:
            cls_result = classify_phone(
                image,
                bbox,
                direct_model_id=direct_model_id,
                direct_confidence=confidence
            )
            if cls_result is None:
                message = (
                    "Đã thấy điện thoại trong ảnh nhưng chưa xác định được dòng máy. Hãy tải ảnh mặt lưng rõ hơn "
                    "hoặc chọn model 3D thủ công."
                    if source == "upload"
                    else "Chưa nhận diện rõ cụm camera. Hãy chụp gần hơn, đủ sáng và đặt mặt lưng điện thoại hướng vào camera."
                )
                return {
                    "success": False,
                    "phone_detected": False,
                    "model_recognized": False,
                    "message": message
                }
            detected_phone_id = cls_result["model_id"]
            phone_model_name = cls_result["model_name"]
            device_code = cls_result["device_code"]
            case_model_url = cls_result["case_model_url"]
            confidence = cls_result["confidence"]
        else:
            return {
                "success": False,
                "phone_detected": False,
                "model_recognized": False,
                "message": "Bộ phân loại model chưa được tải. Hãy kiểm tra AI Service."
            }

        # Cắt ảnh điện thoại để đưa vào ROCA 6DoF Alignment
        x1, y1, x2, y2 = bbox
        cropped = image[max(0, y1):min(h, y2), max(0, x1):min(w, x2)]
        if cropped.size == 0:
            cropped = image

        pose = None
        if detected_phone_id is not None and roca_pipeline is not None:
            try:
                roca_res = roca_pipeline.infer(cropped, matched_model_id=detected_phone_id)
                pose = {
                    "rotation": roca_res["rotation_matrix"],
                    "translation": roca_res["translation_vector"],
                    "scale": roca_res["predicted_scale"]
                }
            except Exception as e:
                print(f"Lỗi tính ROCA pose: {e}")

        return {
            "success": True,
            "phone_detected": True,
            "phone_model_id": detected_phone_id,
            "phone_model_name": phone_model_name,
            "model_recognized": True,
            "device_code": device_code,
            "case_model_url": case_model_url,
            "confidence": round(confidence, 4),
            "bbox": bbox,
            "pose_6dof": pose,
            "message": f"AI đã nhận diện: {phone_model_name} ({round(confidence * 100, 1)}%)"
        }

if __name__ == "__main__":
    if HAS_FASTAPI:
        import uvicorn  # type: ignore
        uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=True)
    else:
        print("Vui lòng cài đặt thư viện: pip install -r requirements.txt")
