import numpy as np

class PlateDetector:
    def __init__(self):
        # We disabled ONNX runtime dependency and YOLO to avoid protobuf errors.
        # Now we process direct frames using PaddleOCR DB-Text Detector natively.
        self.session = None

    def detect(self, frame: np.ndarray):
        """
        No-op detector because PaddleOCR natively does the detection and 
        recognition simultaneously, bypassing the need for a separate YOLO step.
        Returns: Full frame bounding box
        """
        h, w = frame.shape[:2]
        return [([0, 0, w, h], 1.0)]
