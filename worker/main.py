import os
import time
import cv2
import requests
import numpy as np
import redis
import json
import structlog
import threading
from ocr import PlateOCR

# Configure structured logger
logger = structlog.get_logger()

# Environment variables
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://127.0.0.1:8000")
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
LPR_WORKER_API_KEY = os.getenv("LPR_WORKER_API_KEY", "ariot-lpr-worker-shared-secure-token-2026")

# Initialize Redis client
try:
    r_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, socket_timeout=3)
    r_client.ping()
    logger.info("Connected to Redis successfully")
except Exception as err:
    logger.error("Failed to connect to Redis", error=str(err))
    r_client = None


def compute_iou(box1, box2):
    xA = max(box1[0], box2[0])
    yA = max(box1[1], box2[1])
    xB = min(box1[2], box2[2])
    yB = min(box1[3], box2[3])

    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (box1[2] - box1[0]) * (box1[3] - box1[1])
    boxBArea = (box2[2] - box2[0]) * (box2[3] - box2[1])

    if float(boxAArea + boxBArea - interArea) == 0:
        return 0.0

    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou


class CentroidTracker:
    def __init__(self, max_disappeared=15, max_window_size=12):
        self.next_object_id = 0
        self.objects = {}       # id -> last bounding box
        self.disappeared = {}   # id -> frames count
        self.voting_cache = {}  # id -> dict of candidates
        self.sent_plates = {}   # id -> set of plates already posted
        self.total_frames_tracked = {} # id -> total valid frames processed
        self.max_disappeared = max_disappeared
        self.max_window_size = max_window_size

    def register(self, bbox):
        self.objects[self.next_object_id] = bbox
        self.disappeared[self.next_object_id] = 0
        self.voting_cache[self.next_object_id] = []
        self.sent_plates[self.next_object_id] = set()
        self.total_frames_tracked[self.next_object_id] = 0
        self.next_object_id += 1
        return self.next_object_id - 1

    def deregister(self, object_id):
        del self.objects[object_id]
        del self.disappeared[object_id]
        self.sent_plates.pop(object_id, None)
        self.total_frames_tracked.pop(object_id, None)
        raw_list = self.voting_cache.pop(object_id, [])
        report = {}
        for item in raw_list:
            p = item["plate"]
            if p not in report:
                report[p] = {"count": 0, "sum_conf": 0.0, "review": False, "crop": item["crop"]}
            report[p]["count"] += 1
            report[p]["sum_conf"] += item["confidence"]
            if item["review_needed"]:
                report[p]["review"] = True
        return report


    def update(self, detected_bboxes):
        deregistered_reports = []

        if len(detected_bboxes) == 0:
            for object_id in list(self.objects.keys()):
                self.disappeared[object_id] += 1
                if self.disappeared[object_id] > self.max_disappeared:
                    report = self.deregister(object_id)
                    if report:
                        deregistered_reports.append((object_id, report))
            return [], deregistered_reports

        input_ids = list(self.objects.keys())
        input_bboxes = list(self.objects.values())

        if len(self.objects) == 0:
            for bbox in detected_bboxes:
                self.register(bbox)
        else:
            matched_indices = []
            for d_bbox in detected_bboxes:
                best_iou = 0.0
                best_id = -1
                for o_idx, o_id in enumerate(input_ids):
                    iou = compute_iou(input_bboxes[o_idx], d_bbox)
                    if iou > best_iou and iou > 0.15:
                        best_id = o_id
                        best_iou = iou

                if best_id != -1 and best_id not in matched_indices:
                    self.objects[best_id] = d_bbox
                    self.disappeared[best_id] = 0
                    matched_indices.append(best_id)
                else:
                    self.register(d_bbox)

            for o_id in input_ids:
                if o_id not in matched_indices:
                    self.disappeared[o_id] += 1
                    if self.disappeared[o_id] > self.max_disappeared:
                        report = self.deregister(o_id)
                        if report:
                            deregistered_reports.append((o_id, report))

        active = [(o_id, bbox) for o_id, bbox in self.objects.items()]
        return active, deregistered_reports


def authenticate_worker():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            url = f"{BACKEND_API_URL}/health"
            res = requests.get(url, timeout=3)
            if res.status_code == 200:
                logger.info("Worker authenticated successfully with Backend API")
                return True
        except Exception as e:
            logger.warning("Backend API authentication attempt failed", attempt=attempt, error=str(e))
        time.sleep(2)
    return False


def get_active_cameras():
    try:
        url = f"{BACKEND_API_URL}/api/cameras/worker/active"
        headers = {
            "X-API-KEY": LPR_WORKER_API_KEY
        }
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            return res.json()
    except Exception as e:
        logger.error("Failed to load active cameras", error=str(e))
    return []


# Duplicate detection suppression
LAST_SENT_TIMES = {}


def send_plate_to_backend(plate, confidence, crop_img, review_needed, camera_id):
    try:
        # Central duplicate suppression (5 seconds cooldown)
        last_sent = LAST_SENT_TIMES.get(plate, 0.0)
        if time.time() - last_sent < 5.0:
            logger.info("Duplicate detection suppressed by cooldown", plate=plate, elapsed=time.time() - last_sent)
            return

        LAST_SENT_TIMES[plate] = time.time()

        if crop_img is not None and crop_img.size > 0:
            _, buffer = cv2.imencode('.jpg', crop_img)
            import base64
            img_b64 = base64.b64encode(buffer).decode('utf-8')
        else:
            img_b64 = None

        payload = {
            "plate_number": plate,
            "confidence": float(confidence),
            "camera_id": camera_id,
            "direction": "IN",
            "ocr_confidence": float(confidence),
            "ai_confidence": float(confidence),
            "snapshot_path": "pending_snapshot.jpg",
            "plate_crop_path": "pending_crop.jpg",
            "review_needed": bool(review_needed)
        }
        headers = {
            "X-API-KEY": LPR_WORKER_API_KEY
        }
        url = f"{BACKEND_API_URL}/api/access-logs/detect"
        res = requests.post(url, json=payload, headers=headers, timeout=5)
        if res.status_code == 201:
            logger.info("Detection logged successfully", plate=plate, review=review_needed)
            return True
        else:
            logger.error("Failed to log detection", code=res.status_code, body=res.text)
    except Exception as e:
        logger.error("Error sending detection to backend", error=str(e))
    return False


class FreshFrameReader:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = cv2.VideoCapture(self.rtsp_url)
        self.lock = threading.Lock()
        self.running = True
        self.frame = None
        self.ret = False
        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _update(self):
        while self.running:
            with self.lock:
                if not self.cap.isOpened():
                    self.cap.release()
                    self.cap = cv2.VideoCapture(self.rtsp_url)
                    time.sleep(2)
                    continue
            ret, frame = self.cap.read()
            if not ret:
                logger.warning("RTSP stream frame capture failure. Reconnecting...")
                time.sleep(2)
                with self.lock:
                    self.cap.release()
                    self.cap = cv2.VideoCapture(self.rtsp_url)
                continue
            with self.lock:
                self.frame = frame
                self.ret = ret
            time.sleep(0.01)

    def read(self):
        with self.lock:
            if self.frame is None:
                return False, None
            return self.ret, self.frame.copy()

    def isOpened(self):
        with self.lock:
            return self.cap.isOpened()

    def release(self):
        self.running = False
        self.thread.join(timeout=1)
        with self.lock:
            self.cap.release()


def main():
    if not authenticate_worker():
        logger.error("Worker authentication failed. Exiting.")
        return

    ocr_engine = PlateOCR()
    
    trackers = {}
    readers = {}
    last_camera_sync = 0

    logger.info("Starting LPR dynamic multi-camera worker loop")

    while True:
        # Sync cameras every 30 seconds
        if time.time() - last_camera_sync > 30:
            cameras = get_active_cameras()
            active_ids = set()
            for cam in cameras:
                cam_id = cam["id"]
                cam_url = cam.get("url", cam.get("rtsp_url"))
                if not cam_url:
                    continue
                active_ids.add(cam_id)
                if cam_id not in readers:
                    logger.info("Adding new camera stream", camera_id=cam_id, url=cam_url)
                    readers[cam_id] = FreshFrameReader(cam_url)
                    trackers[cam_id] = CentroidTracker(max_disappeared=15, max_window_size=12)
            
            # Remove deleted cameras
            for cam_id in list(readers.keys()):
                if cam_id not in active_ids:
                    logger.info("Removing deleted camera stream", camera_id=cam_id)
                    readers[cam_id].release()
                    del readers[cam_id]
                    del trackers[cam_id]
                    
            last_camera_sync = time.time()

        if not readers:
            time.sleep(1)
            continue

        for camera_id, reader in list(readers.items()):
            ret, frame = reader.read()
            if not ret or frame is None:
                continue

            try:
                plate, confidence, crop_img, review_needed = ocr_engine.read_plate(frame)
            except Exception as ocr_err:
                logger.error("OCR engine read_plate error on frame", error=str(ocr_err))
                plate, confidence, crop_img, review_needed = "", 0.0, None, True

            detected_bboxes = []
            if plate and confidence >= 0.85 and crop_img is not None:
                h, w = frame.shape[:2]
                detected_bboxes.append([w // 4, h // 4, w * 3 // 4, h * 3 // 4])

            tracker = trackers[camera_id]
            active_trackers, deregistered_reports = tracker.update(detected_bboxes)

            if detected_bboxes and active_trackers:
                matched_id = active_trackers[-1][0]
                tracker.total_frames_tracked[matched_id] += 1
                total_valid_frames = tracker.total_frames_tracked[matched_id]

                tracker.voting_cache[matched_id].append({
                    "plate": plate,
                    "confidence": confidence,
                    "review_needed": review_needed,
                    "crop": crop_img
                })
                
                if len(tracker.voting_cache[matched_id]) > tracker.max_window_size:
                    tracker.voting_cache[matched_id].pop(0)

                cache = {}
                for item in tracker.voting_cache[matched_id]:
                    p = item["plate"]
                    if p not in cache:
                        cache[p] = {"count": 0, "sum_conf": 0.0, "review": False, "crop": item["crop"]}
                    cache[p]["count"] += 1
                    cache[p]["sum_conf"] += item["confidence"]
                    if item["review_needed"]:
                        cache[p]["review"] = True

                freq = cache[plate]["count"] if plate in cache else 0

                if freq >= 5 and plate not in tracker.sent_plates[matched_id]:
                    candidates_list = []
                    for p_str, info in cache.items():
                        c_freq = info["count"]
                        if c_freq > 0:
                            avg_c_conf = info["sum_conf"] / c_freq
                            weight = avg_c_conf * np.log(c_freq + 1)
                            candidates_list.append((p_str, weight, info))
                    
                    candidates_list.sort(key=lambda x: x[1], reverse=True)
                    
                    if candidates_list:
                        top_plate, top_weight, top_info = candidates_list[0]
                        if top_plate == plate:
                            is_ambiguous = False
                            if len(candidates_list) > 1:
                                runner_plate, runner_weight, _ = candidates_list[1]
                                if (top_weight - runner_weight) / top_weight < 0.15:
                                    is_ambiguous = True

                            final_review = top_info["review"] or is_ambiguous or (top_info["sum_conf"] / freq < 0.85)
                            
                            tracker.sent_plates[matched_id].add(plate)
                            send_plate_to_backend(
                                plate=plate,
                                confidence=top_info["sum_conf"] / freq,
                                crop_img=top_info["crop"],
                                review_needed=final_review,
                                camera_id=camera_id
                            )

            for object_id, report in deregistered_reports:
                if not report:
                    continue

                total_votes = sum(item["count"] for item in report.values())
                if total_votes < 4:
                    continue

                candidates_weighted = []
                for p_str, info in report.items():
                    freq = info["count"]
                    if freq > 0:
                        avg_conf = info["sum_conf"] / freq
                        weight = avg_conf * np.log(freq + 1)
                        candidates_weighted.append((p_str, weight, info))

                candidates_weighted.sort(key=lambda x: x[1], reverse=True)
                if not candidates_weighted:
                    continue

                top_plate, top_weight, top_info = candidates_weighted[0]
                top_freq = top_info["count"]

                if top_freq < (total_votes // 2) + 1:
                    continue

                if object_id in tracker.sent_plates and top_plate in tracker.sent_plates[object_id]:
                    continue

                is_ambiguous = False
                if len(candidates_weighted) > 1:
                    runner_plate, runner_weight, _ = candidates_weighted[1]
                    if (top_weight - runner_weight) / top_weight < 0.15:
                        is_ambiguous = True

                final_review = top_info["review"] or is_ambiguous or (top_info["sum_conf"] / top_freq < 0.85)

                send_plate_to_backend(
                    plate=top_plate,
                    confidence=top_info["sum_conf"] / top_freq,
                    crop_img=top_info["crop"],
                    review_needed=final_review,
                    camera_id=camera_id
                )
        
        time.sleep(0.01)


if __name__ == "__main__":
    main()
