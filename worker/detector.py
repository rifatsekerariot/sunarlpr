import os
import cv2
import numpy as np
import onnxruntime as ort
import structlog
from config import worker_config

logger = structlog.get_logger()

class PlateDetector:
    def __init__(self):
        self.model_path = worker_config.YOLO_MODEL_PATH
        self.conf_threshold = worker_config.DETECTION_CONFIDENCE_THRESHOLD
        
        # Load ONNX model if present, otherwise log warning (fallback to mock detection if file is missing during startup)
        if os.path.exists(self.model_path):
            try:
                # CPU execution provider. In GPU deployments, CUDAExecutionProvider would be added first.
                self.session = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
                self.input_name = self.session.get_inputs()[0].name
                self.output_names = [out.name for out in self.session.get_outputs()]
                logger.info("YOLO ONNX model loaded successfully", path=self.model_path)
            except Exception as e:
                logger.error("Failed to load YOLO ONNX model", error=str(e))
                self.session = None
        else:
            logger.warning("ONNX model file not found, running mock detections for development/demo streams", path=self.model_path)
            self.session = None

    def preprocess(self, frame: np.ndarray, target_size=(640, 640)):
        # Normalize and pad frame
        h, w, c = frame.shape
        scale = min(target_size[0] / h, target_size[1] / w)
        nh = int(h * scale)
        nw = int(w * scale)
        
        resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
        
        # Letterbox padding
        top = (target_size[0] - nh) // 2
        bottom = target_size[0] - nh - top
        left = (target_size[1] - nw) // 2
        right = target_size[1] - nw - left
        
        padded = cv2.copyMakeBorder(resized, top, bottom, left, right, cv2.BORDER_CONSTANT, value=(114, 114, 114))
        
        # HWC to CHW, scaling to [0, 1]
        img = padded.transpose((2, 0, 1))[::-1]  # BGR to RGB
        img = np.ascontiguousarray(img).astype(np.float32) / 255.0
        img = np.expand_dims(img, axis=0)
        
        return img, scale, (left, top)

    def detect(self, frame: np.ndarray):
        """
        Detects plate bounding boxes inside the frame.
        Returns: List of tuples (box, confidence) where box is [x1, y1, x2, y2]
        """
        if self.session is None:
            # Simulation/Mock logic for development where actual physical YOLO model isn't placed yet.
            # If frame size permits, we simulate finding a plate near the center of the screen 2% of the time.
            if np.random.rand() < 0.05:
                h, w = frame.shape[:2]
                x1, y1 = int(w * 0.4), int(h * 0.6)
                x2, y2 = int(w * 0.6), int(h * 0.7)
                return [([x1, y1, x2, y2], 0.92)]
            return []

        img, scale, (pad_x, pad_y) = self.preprocess(frame)
        outputs = self.session.run(self.output_names, {self.input_name: img})
        
        # Process outputs (YOLO11 outputs [batch, 84, 8400] or similar depending on classes and anchors)
        output = outputs[0][0] # [84, 8400]
        # Transpose to [8400, 84]
        output = output.T
        
        boxes = []
        confidences = []
        
        for row in output:
            # First 4 elements are x_center, y_center, width, height
            # 5th element is plate class probability (since we train a 1-class detector for plates)
            conf = row[4]
            if conf > self.conf_threshold:
                xc, yc, w, h = row[0:4]
                
                # Rescale back to original image coordinates
                x1 = int((xc - w/2 - pad_x) / scale)
                y1 = int((yc - h/2 - pad_y) / scale)
                x2 = int((xc + w/2 - pad_x) / scale)
                y2 = int((yc + h/2 - pad_y) / scale)
                
                # Clip to image boundaries
                ih, iw = frame.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(iw, x2), min(ih, y2)
                
                boxes.append([x1, y1, x2, y2])
                confidences.append(float(conf))
                
        # NMS to clear redundant overlaps
        # Convert [x1, y1, x2, y2] to [x1, y1, width, height] for NMSBoxes
        nms_boxes = [[b[0], b[1], b[2] - b[0], b[3] - b[1]] for b in boxes]
        indices = cv2.dnn.NMSBoxes(nms_boxes, confidences, self.conf_threshold, self.nms_threshold)
        
        results = []
        if len(indices) > 0:
            for idx in indices.flatten():
                results.append((boxes[idx], confidences[idx]))
                
        return results
