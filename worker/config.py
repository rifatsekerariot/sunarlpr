import os

class WorkerConfig:
    BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://backend:8000")
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://redis:6379/0")
    MEDIA_ROOT: str = os.getenv("MEDIA_ROOT", "/app/media")
    
    # YOLO Settings
    # Path to YOLO11n ONNX model inside docker container
    YOLO_MODEL_PATH: str = os.getenv("YOLO_MODEL_PATH", "/app/models/yolo11n_plate.onnx")
    DETECTION_CONFIDENCE_THRESHOLD: float = 0.50
    
    # OCR Settings
    OCR_CONFIDENCE_THRESHOLD: float = 0.60
    
    # RTSP Camera mapping (Camera UUID -> RTSP Stream or Video file path)
    # Inside docker compose, we can mount sample video files or point to RTSP addresses.
    CAMERAS = {
        "8f8f8f8f-8f8f-8f8f-8f8f-8f8f8f8f8f8f": {
            "name": "Ana Kapi Giris",
            "rtsp_url": os.getenv("CAMERA_1_URL", "/app/test_media/sample_in.mp4"),
            "direction": "IN"
        }
    }

worker_config = WorkerConfig()
