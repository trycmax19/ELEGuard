
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_DIR / "eleguard_events.db"
MODEL_PATH = PROJECT_DIR / "yolo11n.pt"

APP_NAME = "EleGuard AI"
DEFAULT_CONFIDENCE = 0.35
DEFAULT_ALERT_COOLDOWN = 30
IMAGE_SIZE = 640

# COCO class ID for elephant in the standard YOLO model.
ELEPHANT_CLASS_ID = 20

# This is a demonstration prototype, not a railway safety system.
SAFETY_NOTICE = (
    "Prototype only. Elephant detection does not establish train "
    "position, distance to railway tracks, or collision risk. "
    "Do not use this application for operational railway decisions."
)
