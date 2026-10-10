
import alerts
import database


def test_alert_cooldown(tmp_path, monkeypatch):
    test_db = tmp_path / "test_alerts.db"
    monkeypatch.setattr(database, "DATABASE_PATH", test_db)
    database.init_db()

    # AlertManager imports log_event directly, so patch its reference too.
    monkeypatch.setattr(alerts, "log_event", database.log_event)

    manager = alerts.AlertManager(cooldown_seconds=30)

    assert manager.record_detection(1, 0.9) is True
    assert manager.record_detection(1, 0.9) is False

    events = database.get_events()
    assert len(events) == 1
