import cv2
import re
import numpy as np
import structlog
from paddleocr import PaddleOCR

logger = structlog.get_logger()

# Highly tolerant plate match:
# Matches 5 to 9 alphanumeric characters (letters and numbers)
# Tolerant to OCR typos or minor character drops common in distant reads
PLATE_REGEX = re.compile(r"^[A-Z0-9]{5,9}$")

class PlateOCR:
    def __init__(self):
        try:
            # Initialize PaddleOCR with Turkish / English characters
            # use_space_char=False avoids splitting plate letters and numbers (e.g. 34 MNF 893 -> 34MNF893)
            self.ocr = PaddleOCR(lang='tr', use_space_char=False)
            logger.info("PaddleOCR engine loaded successfully")
        except Exception as e:
            logger.warning("PaddleOCR loading failed, using fallback regex simulation for dev testing", error=str(e))
            self.ocr = None

    def clean_text(self, text: str) -> str:
        cleaned = re.sub(r"[^A-Z0-9]", "", text.upper())
        return cleaned

    def validate_plate(self, text: str) -> bool:
        cleaned = self.clean_text(text)
        match = PLATE_REGEX.match(cleaned)
        return match is not None

    def read_plate(self, frame: np.ndarray):
        """
        Processes the entire camera frame with PaddleOCR Text Detector.
        If a plate is found:
          - Extracts the crop area using coordinate bounding boxes.
          - Concatenates split plate components (e.g. '34MNF' + '893').
        Returns: Tuple (plate_text, confidence, crop_image)
        """
        if self.ocr is None or frame is None or frame.size == 0:
            return "", 0.0, None

        try:
            # 1. Bicubic Zoom (2.0x) on the input frame to make distant plates larger and crisper
            h, w = frame.shape[:2]
            resized = cv2.resize(frame, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
            
            # Detect text boxes and read contents
            result = self.ocr.ocr(resized, cls=False)
            if not result or not result[0]:
                return "", 0.0, None
                
            best_plate = ""
            best_conf = 0.0
            best_box = None
            
            candidates = []
            for line in result[0]:
                if not line or len(line) < 2:
                    continue
                box, text_info = line
                if not text_info or len(text_info) < 2:
                    continue
                raw_text, confidence = text_info
                cleaned_text = self.clean_text(raw_text)
                if len(cleaned_text) >= 2:
                    # Rescale coordinates back to original frame size
                    orig_box = [[pt[0] / 2.0, pt[1] / 2.0] for pt in box]
                    candidates.append((orig_box, cleaned_text, float(confidence)))

            if not candidates:
                return "", 0.0, None

            # Sort candidates left-to-right based on bounding box X coordinate
            candidates.sort(key=lambda c: c[0][0][0])
            
            # 1. First check if any individual candidate is a valid plate
            for box, text, conf in candidates:
                if self.validate_plate(text):
                    if conf > best_conf:
                        best_plate = text
                        best_conf = conf
                        best_box = box

            # 2. Try merging adjacent candidates (e.g. '34MNF' + '893' -> '34MNF893')
            if not best_plate and len(candidates) >= 2:
                for i in range(len(candidates) - 1):
                    box1, text1, conf1 = candidates[i]
                    box2, text2, conf2 = candidates[i+1]
                    
                    # Check if they are on a similar vertical level (Y axis overlap)
                    y1_center = (box1[0][1] + box1[2][1]) / 2
                    y2_center = (box2[0][1] + box2[2][1]) / 2
                    h1 = abs(box1[2][1] - box1[0][1])
                    
                    # If vertical distance is small, they are in the same line
                    if abs(y1_center - y2_center) < (h1 * 0.8):
                        merged_text = text1 + text2
                        if self.validate_plate(merged_text):
                            best_plate = merged_text
                            best_conf = (conf1 + conf2) / 2
                            # Bounding box covering both segments
                            best_box = [
                                [min(box1[0][0], box2[0][0]), min(box1[0][1], box2[0][1])],
                                [max(box1[1][0], box2[1][0]), min(box1[1][1], box2[1][1])],
                                [max(box1[2][0], box2[2][0]), max(box1[2][1], box2[2][1])],
                                [min(box1[3][0], box2[3][0]), max(box1[3][1], box2[3][1])]
                            ]
                            break
            
            if best_plate and best_box:
                # Bounding box is coordinates of [top_left, top_right, bottom_right, bottom_left]
                xs = [pt[0] for pt in best_box]
                ys = [pt[1] for pt in best_box]
                x1, y1 = max(0, int(min(xs))), max(0, int(min(ys)))
                x2, y2 = min(w, int(max(xs))), min(h, int(max(ys)))
                
                # Add a tiny padding around the crop area for aesthetic looks on dashboard
                pad_w = int((x2 - x1) * 0.1)
                pad_h = int((y2 - y1) * 0.1)
                cx1 = max(0, x1 - pad_w)
                cy1 = max(0, y1 - pad_h)
                cx2 = min(w, x2 + pad_w)
                cy2 = min(h, y2 + pad_h)
                
                crop_img = frame[cy1:cy2, cx1:cx2]
                logger.info("Plate OCR detected from candidates", plate=best_plate, conf=best_conf)
                return best_plate, best_conf, crop_img
                
            return "", 0.0, None
            
        except Exception as e:
            logger.error("OCR execution error", error=str(e))
            return "", 0.0, None
