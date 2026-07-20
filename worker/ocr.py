import cv2
import re
import numpy as np
import structlog
import traceback
from paddleocr import PaddleOCR

logger = structlog.get_logger()

# Strict Turkish Plate Pattern Layout Rules (City Code 01-81 + Letters + Digits)
STRICT_PLATE_REGEXES = [
    re.compile(r"^(0[1-9]|[1-7][0-9]|8[0-1])[A-Z]\d{4}$"),
    re.compile(r"^(0[1-9]|[1-7][0-9]|8[0-1])[A-Z]{2}\d{3}$"),
    re.compile(r"^(0[1-9]|[1-7][0-9]|8[0-1])[A-Z]{3}\d{2}$"),
    re.compile(r"^(0[1-9]|[1-7][0-9]|8[0-1])[A-Z]{2}\d{4}$"),
    re.compile(r"^(0[1-9]|[1-7][0-9]|8[0-1])[A-Z]{3}\d{3}$"),
    re.compile(r"^(0[1-9]|[1-7][0-9]|8[0-1])[A-Z]{1,4}\d{1,4}$"),
]

# Lexicon mappings to correct typical OCR typos contextually
TO_DIGIT = {"O": "0", "I": "1", "T": "1", "B": "8", "S": "5", "Z": "2", "G": "6"}
TO_LETTER = {"0": "O", "1": "I", "8": "B", "5": "S", "2": "Z", "6": "G"}

class PlateOCR:
    def __init__(self):
        try:
            self.ocr = PaddleOCR(lang='en', ocr_version='PP-OCRv4')
            logger.info("PaddleOCR engine loaded successfully")
        except Exception as e:
            logger.warning("PaddleOCR loading failed", error=str(e))
            self.ocr = None

    def clean_text(self, text: str) -> str:
        return re.sub(r"[^A-Z0-9]", "", text.upper())

    def check_strict_layout(self, text: str) -> bool:
        cleaned = self.clean_text(text)
        for regex in STRICT_PLATE_REGEXES:
            if regex.match(cleaned):
                return True
        return False

    def try_positional_fixes(self, text: str) -> str:
        cleaned = list(self.clean_text(text))
        n = len(cleaned)
        if n < 5 or n > 9:
            return "".join(cleaned)

        # 1. First 2 characters must be digits (01-81)
        for i in range(2):
            if cleaned[i] in TO_DIGIT:
                cleaned[i] = TO_DIGIT[cleaned[i]]

        # 2. Last 2 characters must be digits
        for i in range(n - 2, n):
            if cleaned[i] in TO_DIGIT:
                cleaned[i] = TO_DIGIT[cleaned[i]]

        # 3. Middle segment must be letters
        letter_end = n - 2
        if n == 5:    # 34A12
            letter_end = 3
        elif n == 6:  # 34A123 or 34AB12
            letter_end = 3 if cleaned[3].isdigit() else 4
        elif n == 7:  # 34AB123 or 34ABC12
            letter_end = 4 if cleaned[4].isdigit() else 5
        elif n == 8:  # 34ABC123 or 34AB1234
            letter_end = 5 if cleaned[5].isdigit() else 4

        for i in range(2, letter_end):
            if cleaned[i] == "8":
                cleaned[i] = "F"
            elif cleaned[i] in TO_LETTER:
                cleaned[i] = TO_LETTER[cleaned[i]]

        return "".join(cleaned)

    def read_plate(self, frame: np.ndarray):
        if self.ocr is None or frame is None or frame.size == 0:
            return "", 0.0, None, True

        try:
            h, w = frame.shape[:2]
            resized = cv2.resize(frame, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
            
            result = self.ocr.ocr(resized, cls=False)
            # Safe validation of Nested Lists returned by PaddleOCR
            if not result or not isinstance(result, list) or len(result) == 0 or result[0] is None:
                return "", 0.0, None, True
                
            candidates = []
            for line in result[0]:
                if not line or not isinstance(line, list) or len(line) < 2:
                    continue
                box = line[0]
                text_info = line[1]
                if not text_info or len(text_info) < 2:
                    continue
                raw_text, confidence = text_info
                cleaned_text = self.clean_text(raw_text)
                
                # Scale coordinates back
                orig_box = [[pt[0] / 2.0, pt[1] / 2.0] for pt in box]
                candidates.append((orig_box, cleaned_text, float(confidence)))

            if not candidates:
                return "", 0.0, None, True

            best_plate = ""
            best_conf = 0.0
            best_box = None
            review_needed = False

            # Check individual candidates first
            for box, text, conf in candidates:
                if self.check_strict_layout(text):
                    if conf > best_conf:
                        best_plate = text
                        best_conf = conf
                        best_box = box
                        review_needed = (conf < 0.85)
                else:
                    fixed_text = self.try_positional_fixes(text)
                    if self.check_strict_layout(fixed_text):
                        if conf > best_conf:
                            best_plate = fixed_text
                            best_conf = conf
                            best_box = box
                            review_needed = True

            # Yatay birleştirme
            if not best_plate and len(candidates) >= 2:
                candidates.sort(key=lambda c: c[0][0][0])
                for length in range(2, len(candidates) + 1):
                    if best_plate:
                        break
                    for i in range(len(candidates) - length + 1):
                        sub_cands = candidates[i:i+length]
                        
                        valid_line = True
                        base_y = (sub_cands[0][0][0][1] + sub_cands[0][0][2][1]) / 2
                        base_h = abs(sub_cands[0][0][2][1] - sub_cands[0][0][0][1])
                        for c in sub_cands[1:]:
                            c_y = (c[0][0][1] + c[0][2][1]) / 2
                            if abs(base_y - c_y) > (base_h * 0.8):
                                valid_line = False
                                break
                                
                        if not valid_line:
                            continue
                            
                        merged = "".join(c[1] for c in sub_cands)
                        conf = sum(c[2] for c in sub_cands) / length
                        
                        if self.check_strict_layout(merged):
                            best_plate = merged
                            best_conf = conf
                            review_needed = (best_conf < 0.85)
                            best_box = [
                                [min(c[0][0][0] for c in sub_cands), min(c[0][0][1] for c in sub_cands)],
                                [max(c[0][1][0] for c in sub_cands), min(c[0][1][1] for c in sub_cands)],
                                [max(c[0][2][0] for c in sub_cands), max(c[0][2][1] for c in sub_cands)],
                                [min(c[0][3][0] for c in sub_cands), max(c[0][3][1] for c in sub_cands)]
                            ]
                            break
                        else:
                            fixed_merged = self.try_positional_fixes(merged)
                            if self.check_strict_layout(fixed_merged):
                                best_plate = fixed_merged
                                best_conf = conf
                                review_needed = True
                                best_box = [
                                    [min(c[0][0][0] for c in sub_cands), min(c[0][0][1] for c in sub_cands)],
                                    [max(c[0][1][0] for c in sub_cands), min(c[0][1][1] for c in sub_cands)],
                                    [max(c[0][2][0] for c in sub_cands), max(c[0][2][1] for c in sub_cands)],
                                    [min(c[0][3][0] for c in sub_cands), max(c[0][3][1] for c in sub_cands)]
                                ]
                                break

            # Dikey birleştirme
            if not best_plate and len(candidates) >= 2:
                candidates.sort(key=lambda c: c[0][0][1])
                for length in range(2, len(candidates) + 1):
                    if best_plate:
                        break
                    for i in range(len(candidates) - length + 1):
                        sub_cands = candidates[i:i+length]
                        
                        valid_col = True
                        base_x = (sub_cands[0][0][0][0] + sub_cands[0][0][1][0]) / 2
                        base_w = abs(sub_cands[0][0][1][0] - sub_cands[0][0][0][0])
                        for c in sub_cands[1:]:
                            c_x = (c[0][0][0] + c[0][1][0]) / 2
                            if abs(base_x - c_x) > (base_w * 0.9):
                                valid_col = False
                                break
                                
                        if not valid_col:
                            continue
                            
                        merged = "".join(c[1] for c in sub_cands)
                        conf = sum(c[2] for c in sub_cands) / length
                        
                        if self.check_strict_layout(merged):
                            best_plate = merged
                            best_conf = conf
                            review_needed = (best_conf < 0.85)
                            best_box = [
                                [min(c[0][0][0] for c in sub_cands), min(c[0][0][1] for c in sub_cands)],
                                [max(c[0][1][0] for c in sub_cands), min(c[0][1][1] for c in sub_cands)],
                                [max(c[0][2][0] for c in sub_cands), max(c[0][2][1] for c in sub_cands)],
                                [min(c[0][3][0] for c in sub_cands), max(c[0][3][1] for c in sub_cands)]
                            ]
                            break
                        else:
                            fixed_merged = self.try_positional_fixes(merged)
                            if self.check_strict_layout(fixed_merged):
                                best_plate = fixed_merged
                                best_conf = conf
                                review_needed = True
                                best_box = [
                                    [min(c[0][0][0] for c in sub_cands), min(c[0][0][1] for c in sub_cands)],
                                    [max(c[0][1][0] for c in sub_cands), min(c[0][1][1] for c in sub_cands)],
                                    [max(c[0][2][0] for c in sub_cands), max(c[0][2][1] for c in sub_cands)],
                                    [min(c[0][3][0] for c in sub_cands), max(c[0][3][1] for c in sub_cands)]
                                ]
                                break


            if best_plate and best_box:
                xs = [pt[0] for pt in best_box]
                ys = [pt[1] for pt in best_box]
                x1, y1 = max(0, int(min(xs))), max(0, int(min(ys)))
                x2, y2 = min(w, int(max(xs))), min(h, int(max(ys)))
                
                pad_w = int((x2 - x1) * 0.15)
                pad_h = int((y2 - y1) * 0.15)
                cx1 = max(0, x1 - pad_w)
                cy1 = max(0, y1 - pad_h)
                cx2 = min(w, x2 + pad_w)
                cy2 = min(h, y2 + pad_h)
                
                crop_img = frame[cy1:cy2, cx1:cx2]
                logger.info("Stable plate extraction", plate=best_plate, conf=best_conf, review=review_needed)
                return best_plate, best_conf, crop_img, review_needed
                
            return "", 0.0, None, True
            
        except Exception as e:
            logger.error("OCR execution error", error=str(e), traceback=traceback.format_exc())
            return "", 0.0, None, True
