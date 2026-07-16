import os
import cv2
import time
import requests
import datetime
import structlog
from config import worker_config
from detector import PlateDetector
from ocr import PlateOCR

setup_logger = structlog.get_logger()

def send_detection_to_backend(
    plate_number: str,
    camera_id: str,
    direction: str,
    ocr_confidence: float,
    ai_confidence: float,
    frame: cv2.Mat,
    crop: cv2.Mat
):
    # Prepare folder structure: media/YYYY-MM-DD/camera_id/plate_number/
    today_str = datetime.date.today().isoformat()
    dir_path = os.path.join(worker_config.MEDIA_ROOT, today_str, camera_id, plate_number)
    os.makedirs(dir_path, exist_ok=True)
    
    from datetime import timezone
    timestamp_str = datetime.datetime.now(timezone.utc).strftime("%H%M%S_%f")
    snapshot_filename = f"vehicle_{timestamp_str}.jpg"
    crop_filename = f"plate_{timestamp_str}.jpg"
    
    snapshot_full_path = os.path.join(dir_path, snapshot_filename)
    crop_full_path = os.path.join(dir_path, crop_filename)
    
    # Save files on disk
    cv2.imwrite(snapshot_full_path, frame)
    cv2.imwrite(crop_full_path, crop)
    
    # Paths for API (relative to media root)
    api_snapshot_path = f"/media/{today_str}/{camera_id}/{plate_number}/{snapshot_filename}"
    api_crop_path = f"/media/{today_str}/{camera_id}/{plate_number}/{crop_filename}"
    
    payload = {
        "plate_number": plate_number,
        "camera_id": camera_id,
        "direction": direction,
        "ocr_confidence": ocr_confidence,
        "ai_confidence": ai_confidence,
        "snapshot_path": api_snapshot_path,
        "plate_crop_path": api_crop_path
    }
    
    try:
        url = f"{worker_config.BACKEND_API_URL}/api/access-logs/detect"
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code == 201:
            setup_logger.info("Detection logged successfully", plate=plate_number)
        else:
            setup_logger.error("Failed to post detection", status=response.status_code, body=response.text)
    except Exception as e:
        setup_logger.error("Error communicating with backend API", error=str(e))

def run_worker():
    setup_logger.info("Starting LPR camera worker loop")
    detector = PlateDetector()
    ocr_engine = PlateOCR()
    
    # For testing, if we don't have actual RTSP streams, we run a virtual camera loop.
    # We load active cameras from configuration
    cameras = worker_config.CAMERAS
    
    # Open streams/captures
    caps = {}
    for cam_id, info in cameras.items():
        rtsp_url = info["rtsp_url"]
        if rtsp_url == "simulation_rtsp_url" or not rtsp_url:
            setup_logger.warning("No valid RTSP URL configured — camera skipped", camera=info["name"])
            caps[cam_id] = "NO_STREAM"
        else:
            cap = cv2.VideoCapture(rtsp_url)
            if cap.isOpened():
                caps[cam_id] = cap
                setup_logger.info("Stream opened successfully", camera=info["name"], url=rtsp_url)
            else:
                caps[cam_id] = "NO_STREAM"
                setup_logger.warning("Failed to open stream — camera skipped", camera=info["name"])

    frame_count = 0
    frame_skip = 5 # Run inference every 5 frames to optimize CPU utilization

    try:
        while True:
            for cam_id, cap in caps.items():
                cam_info = cameras[cam_id]
                
                if cap == "NO_STREAM":
                    # Stream could not be opened — skip, do not generate mock data
                    time.sleep(5.0)
                    continue

                # Physical Camera processing
                ret, frame = cap.read()
                if not ret:
                    # Loop video if finished
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                    
                frame_count += 1
                if frame_count % frame_skip != 0:
                    continue
                    
                detections = detector.detect(frame)
                for box, ai_conf in detections:
                    x1, y1, x2, y2 = box
                    crop = frame[y1:y2, x1:x2]
                    
                    if crop.size > 0:
                        plate_text, ocr_conf = ocr_engine.read_plate(crop)
                        
                        # Validate confidence and format
                        if plate_text and ocr_conf >= worker_config.OCR_CONFIDENCE_THRESHOLD:
                            send_detection_to_backend(
                                plate_number=plate_text,
                                camera_id=cam_id,
                                direction=cam_info["direction"],
                                ocr_confidence=ocr_conf,
                                ai_confidence=ai_conf,
                                frame=frame,
                                crop=crop
                            )
            time.sleep(0.01) # Avoid 100% CPU lock
    except KeyboardInterrupt:
        setup_logger.info("Worker stopped by operator request")
    finally:
        for cap in caps.values():
            if isinstance(cap, cv2.VideoCapture):
                cap.release()

if __name__ == "__main__":
    run_worker()
