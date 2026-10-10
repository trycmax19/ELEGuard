
import threading

import av
import cv2
from ultralytics import YOLO
from streamlit_webrtc import VideoProcessorBase

from alerts import AlertManager
from config import ELEPHANT_CLASS_ID, IMAGE_SIZE, MODEL_PATH


_model_lock = threading.Lock()


def load_model():
    # YOLO downloads the model weights on first use if needed.
    with _model_lock:
        return YOLO(str(MODEL_PATH))


def detect_image(image_bgr, model, confidence=0.35):
    """Return an annotated image and detection information."""
    results = model.predict(
        source=image_bgr,
        imgsz=IMAGE_SIZE,
        conf=float(confidence),
        verbose=False,
    )

    result = results[0]
    annotated = result.plot()

    elephants = []
    for box in result.boxes:
        class_id = int(box.cls[0])

        if class_id == ELEPHANT_CLASS_ID:
            elephants.append({
                "confidence": float(box.conf[0]),
                "class_id": class_id,
            })

    return {
        "image": annotated,
        "count": len(elephants),
        "confidence": max(
            (item["confidence"] for item in elephants),
            default=0.0,
        ),
    }


class ElephantVideoProcessor(VideoProcessorBase):
    def __init__(self, model, confidence=0.35, cooldown=30):
        self.model = model
        self.confidence = float(confidence)
        self.alert_manager = AlertManager(cooldown)
        self._detection_lock = threading.Lock()
        self._latest_detection = None

    def get_latest_detection(self):
        with self._detection_lock:
            if self._latest_detection is None:
                return None
            return self._latest_detection.copy()

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")

        # Resize large frames to help ordinary laptops.
        height, width = image.shape[:2]
        if width > 960:
            new_height = int(height * 960 / width)
            image = cv2.resize(image, (960, new_height))

        try:
            result = detect_image(
                image,
                self.model,
                self.confidence,
            )
            annotated = result["image"]
            count = result["count"]
            confidence = result["confidence"]

            with self._detection_lock:
                self._latest_detection = (
                    {"count": count, "confidence": confidence}
                    if count
                    else None
                )

            if count:
                label = f"ELEPHANT DETECTED: {count}"
                color = (0, 0, 255)

                self.alert_manager.record_detection(
                    count=count,
                    confidence=confidence,
                    source="webcam",
                )
            else:
                label = "NO ELEPHANT DETECTED IN CURRENT FRAME"
                color = (0, 180, 0)

            cv2.putText(
                annotated,
                label,
                (12, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                color,
                2,
                cv2.LINE_AA,
            )

        except Exception as exc:
            # Keep the camera alive when an individual frame fails.
            with self._detection_lock:
                self._latest_detection = None
            annotated = image.copy()
            cv2.putText(
                annotated,
                f"Detection error: {str(exc)[:65]}",
                (12, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 0, 255),
                2,
            )

        return av.VideoFrame.from_ndarray(
            annotated,
            format="bgr24",
        )
