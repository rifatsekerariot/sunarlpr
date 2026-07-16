import cv2
import re
import numpy as np
import structlog
from paddleocr import PaddleOCR
from config import worker_config

logger = structlog.get_logger()

# Standard Turkish plate regex patterns: 
# 1. 34 ABC 123 (City Code - Letters - Number)
# Matches: 2 digits + 1 to 3 letters + 2 to 4 digits
PLATE_REGEX = re.compile(r"^(0[1-9]|[1-7][0-9]|8[0-1])\s*[a-zA-Z]{1,3}\s*\d{2,4}$")

class PlateOCR:
    def __init__(self):
        try:
            # Initialize PaddleOCR with Turkish / English characters
            # lang='tr' supports Turkish letters (like Ç, Ğ, I, İ, Ö, Ş, Ü) which are common in older plates or custom plates
            self.ocr = PaddleOCR(use_angle_cls=False, lang='tr', show_log=False)
            logger.info("PaddleOCR engine loaded successfully")
        except Exception as e:
            logger.warning("PaddleOCR loading failed, using fallback regex simulation for dev testing", error=str(e))
            self.ocr = None

    def clean_text(self, text: str) -> str:
        # Clean spacing, symbols, and keep letters and digits
        cleaned = re.sub(r"[^A-Z0-9]", "", text.upper())
        return cleaned

    def validate_plate(self, text: str) -> bool:
        # Check standard Turkish plate rules
        # Add basic space formatting back for matching regex: e.g., "34ABC123" -> "34 ABC 123"
        # We search with a loose version of spacing
        cleaned = self.clean_text(text)
        match = PLATE_REGEX.match(cleaned)
        return match is not None

    def read_plate(self, crop: np.ndarray):
        """
        Reads plate text from cropped image.
        Returns: Tuple (plate_text, confidence)
        """
        if self.ocr is None:
            # OCR engine not loaded — return empty, do not generate mock plates
            return "", 0.0

        try:
            result = self.ocr.ocr(crop, cls=False)
            if not result or not result[0]:
                return "", 0.0
                
            # Grab top detection text and conf score
            best_match = result[0][0]
            box, (raw_text, confidence) = best_match
            
            cleaned_text = self.clean_text(raw_text)
            
            logger.info("Plate OCR read complete", raw=raw_text, cleaned=cleaned_text, conf=confidence)
            return cleaned_text, float(confidence)
            
        except Exception as e:
            logger.error("OCR execution error", error=str(e))
            return "", 0.0
