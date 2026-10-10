
import time

from database import log_event


class AlertManager:
    def __init__(self, cooldown_seconds=30):
        self.cooldown_seconds = max(1, int(cooldown_seconds))
        self.last_logged_at = 0.0

    def record_detection(self, count, confidence, source="webcam"):
        now = time.monotonic()

        if now - self.last_logged_at < self.cooldown_seconds:
            return False

        log_event(
            event_type="ELEPHANT_DETECTED",
            count=count,
            confidence=confidence,
            source=source,
        )
        self.last_logged_at = now
        return True
