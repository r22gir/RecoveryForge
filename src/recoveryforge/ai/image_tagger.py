"""
YOLO v8 image recognition and auto-tagging.

Uses ultralytics YOLO v8 for object detection, face detection,
scene classification, and automatic tag generation.
"""

import logging
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from pathlib import Path

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class Detection:
    """Single object detection result."""
    label: str
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]
    class_id: int


@dataclass
class FaceDetection:
    """Face detection result."""
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float
    estimated_age: Optional[int] = None
    estimated_gender: Optional[str] = None


@dataclass
class SceneClassification:
    """Scene classification result."""
    scene_type: str
    confidence: float
    secondary_scenes: List[str] = field(default_factory=list)


@dataclass
class ImageAnalysis:
    """Complete image analysis result."""
    file_path: str
    detections: List[Detection] = field(default_factory=list)
    faces: List[FaceDetection] = field(default_factory=list)
    scene: Optional[SceneClassification] = None
    tags: List[str] = field(default_factory=list)
    error: Optional[str] = None


# Scene keyword mapping for rule-based scene classification
_SCENE_KEYWORDS = {
    "beach": ["wave", "ocean", "sea", "sand", "surf", "shore"],
    "office": ["laptop", "keyboard", "monitor", "desk", "chair", "mouse"],
    "wedding": ["cake", "bouquet", "wedding", "bride", "groom"],
    "nature": ["tree", "flower", "grass", "mountain", "forest", "leaf"],
    "city": ["car", "bus", "building", "traffic", "street", "road"],
    "indoor": ["couch", "sofa", "tv", "refrigerator", "bed", "toilet"],
    "outdoor": ["person", "bicycle", "dog", "cat", "sky", "cloud"],
    "document": ["book", "paper", "text", "receipt", "screenshot"],
    "food": ["pizza", "sandwich", "apple", "banana", "cake", "donut"],
    "animal": ["dog", "cat", "bird", "horse", "cow", "sheep", "elephant"],
}


def _infer_scene(labels: List[str]) -> SceneClassification:
    """Infer scene type from detected object labels."""
    label_set = {lbl.lower() for lbl in labels}
    scores: Dict[str, int] = {}
    for scene, keywords in _SCENE_KEYWORDS.items():
        scores[scene] = sum(1 for kw in keywords if kw in label_set)
    best_scene = max(scores, key=lambda s: scores[s]) if scores else "unknown"
    best_score = scores.get(best_scene, 0)
    secondary = [s for s, cnt in scores.items() if cnt > 0 and s != best_scene]
    confidence = min(1.0, best_score * 0.3) if best_score > 0 else 0.0
    return SceneClassification(
        scene_type=best_scene if best_score > 0 else "unknown",
        confidence=confidence,
        secondary_scenes=secondary,
    )


class AIImageTagger:
    """
    YOLO v8-based image tagger for object detection, face detection,
    scene classification, and automatic tag generation.
    """

    def __init__(self, model_size: str = "nano"):
        """
        Initialize YOLO v8 model.

        Args:
            model_size: Model size - 'nano', 'small', 'medium', or 'large'.
        """
        self.logger = logging.getLogger(__name__)
        self.model_size = model_size
        self._model = None
        self._face_model = None

        _size_map = {"nano": "yolov8n.pt", "small": "yolov8s.pt",
                     "medium": "yolov8m.pt", "large": "yolov8l.pt"}
        self._model_name = _size_map.get(model_size, "yolov8n.pt")

        if not YOLO_AVAILABLE:
            self.logger.warning(
                "ultralytics not installed. AI image tagging will use fallback mode. "
                "Install with: pip install ultralytics"
            )

    def _load_model(self) -> bool:
        """Lazily load the YOLO model."""
        if self._model is not None:
            return True
        if not YOLO_AVAILABLE:
            return False
        try:
            self._model = YOLO(self._model_name)
            return True
        except Exception as e:
            self.logger.error(f"Failed to load YOLO model: {e}")
            return False

    def detect_objects(self, image_path: str) -> List[Detection]:
        """
        Detect objects in an image.

        Args:
            image_path: Path to the image file.

        Returns:
            List of Detection objects with bounding boxes and labels.
        """
        if not Path(image_path).exists():
            self.logger.error(f"Image not found: {image_path}")
            return []

        if not self._load_model():
            return self._fallback_detect(image_path)

        try:
            results = self._model(image_path, verbose=False)
            detections: List[Detection] = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                for i, box in enumerate(boxes):
                    cls_id = int(box.cls[0])
                    label = result.names.get(cls_id, str(cls_id))
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    detections.append(Detection(
                        label=label,
                        confidence=conf,
                        bbox=xyxy,
                        class_id=cls_id,
                    ))
            return detections
        except Exception as e:
            self.logger.error(f"Object detection failed: {e}")
            return []

    def _fallback_detect(self, image_path: str) -> List[Detection]:
        """Fallback detection using basic PIL analysis when YOLO is unavailable."""
        if not PIL_AVAILABLE:
            return []
        try:
            img = Image.open(image_path)
            # Return a minimal placeholder detection indicating an image was found
            return [Detection(
                label="image",
                confidence=1.0,
                bbox=[0.0, 0.0, float(img.width), float(img.height)],
                class_id=0,
            )]
        except Exception:
            return []

    def detect_faces(self, image_path: str) -> List[FaceDetection]:
        """
        Detect faces in an image.

        Args:
            image_path: Path to the image file.

        Returns:
            List of FaceDetection objects.
        """
        if not Path(image_path).exists():
            self.logger.error(f"Image not found: {image_path}")
            return []

        if not self._load_model():
            return []

        try:
            # Use YOLO model's 'person' class as a proxy; a dedicated face model
            # (e.g. yolov8n-face.pt) would be used in production.
            results = self._model(image_path, verbose=False, classes=[0])  # class 0 = person
            faces: List[FaceDetection] = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                for box in boxes:
                    conf = float(box.conf[0])
                    xyxy = box.xyxy[0].tolist()
                    faces.append(FaceDetection(bbox=xyxy, confidence=conf))
            return faces
        except Exception as e:
            self.logger.error(f"Face detection failed: {e}")
            return []

    def classify_scene(self, image_path: str) -> SceneClassification:
        """
        Classify the scene type of an image.

        Args:
            image_path: Path to the image file.

        Returns:
            SceneClassification with scene type and confidence.
        """
        detections = self.detect_objects(image_path)
        labels = [d.label for d in detections]
        return _infer_scene(labels)

    def generate_tags(self, image_path: str) -> List[str]:
        """
        Generate comprehensive tags for an image.

        Args:
            image_path: Path to the image file.

        Returns:
            List of tag strings.
        """
        detections = self.detect_objects(image_path)
        tags: List[str] = []

        # Add object labels as tags (deduplicated, confidence-filtered)
        seen = set()
        for det in detections:
            if det.confidence >= 0.4 and det.label not in seen:
                tags.append(det.label)
                seen.add(det.label)

        # Add scene tag
        scene = _infer_scene([d.label for d in detections])
        if scene.scene_type != "unknown":
            tags.append(f"scene:{scene.scene_type}")

        # Add face tag if faces detected
        faces = self.detect_faces(image_path)
        if faces:
            tags.append("has_faces")
            tags.append(f"faces:{len(faces)}")

        return tags

    def batch_process(
        self,
        image_paths: List[str],
        callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> Dict[str, ImageAnalysis]:
        """
        Process multiple images with an optional progress callback.

        Args:
            image_paths: List of image file paths.
            callback: Optional callable(current, total, path) called after each image.

        Returns:
            Dictionary mapping file path to ImageAnalysis.
        """
        results: Dict[str, ImageAnalysis] = {}
        total = len(image_paths)

        for idx, path in enumerate(image_paths):
            analysis = ImageAnalysis(file_path=path)
            try:
                analysis.detections = self.detect_objects(path)
                analysis.faces = self.detect_faces(path)
                analysis.scene = self.classify_scene(path)
                analysis.tags = self.generate_tags(path)
            except Exception as e:
                analysis.error = str(e)
                self.logger.error(f"Error processing {path}: {e}")

            results[path] = analysis

            if callback:
                try:
                    callback(idx + 1, total, path)
                except Exception:
                    pass

        return results
