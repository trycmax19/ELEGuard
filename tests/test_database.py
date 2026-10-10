
import database


def test_event_can_be_saved_and_retrieved(tmp_path, monkeypatch):
    test_db = tmp_path / "test_events.db"
    monkeypatch.setattr(database, "DATABASE_PATH", test_db)

    database.init_db()

    event_id = database.log_event(
        event_type="ELEPHANT_DETECTED",
        count=2,
        confidence=0.91,
        source="test",
    )

    events = database.get_events()

    assert event_id > 0
    assert len(events) == 1
    assert events.iloc[0]["count"] == 2
    assert events.iloc[0]["source"] == "test"


def test_acknowledgement(tmp_path, monkeypatch):
    test_db = tmp_path / "test_ack.db"
    monkeypatch.setattr(database, "DATABASE_PATH", test_db)

    database.init_db()
    event_id = database.log_event("TEST_EVENT")
    database.acknowledge_event(event_id)

    events = database.get_events()
    assert int(events.iloc[0]["acknowledged"]) == 1
