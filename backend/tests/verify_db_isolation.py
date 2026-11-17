import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, Base, engine
from app.models.telemetry import TelemetryEvent
from app.models.alert import Alert
from app.models.investigation import Investigation, InvestigationStep
from app.models.response import ResponseAction
from app.api.routes.settings import reset_demo_data
from app.services.ingestion.telemetry_service import TelemetryService
from app.services.detection.rule_engine import RuleDetectionEngine

def test_db_isolation():
    db = SessionLocal()

    # 1. Clean state
    reset_demo_data(db)
    db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == False).delete()
    db.commit()

    # 2. Add an explicit LIVE event
    live_event = TelemetryEvent(
        id="EVT-LIVE-AUDIT-99",
        event_type="PROCESS_CREATE",
        user="corp_admin",
        host="PROD-SERVER-01",
        severity="MEDIUM",
        command_line="systeminfo",
        is_demo=False,
        dataset_source="live_siem"
    )
    db.add(live_event)
    db.commit()

    # 3. Load Scenario 1 as DEMO
    demo_json = """[
      {"event_id": "EVT-DEMO-01", "event_type": "AUTH_FAILURE", "user": "victim.user", "host": "WS-01", "is_demo": true},
      {"event_id": "EVT-DEMO-02", "event_type": "AUTH_FAILURE", "user": "victim.user", "host": "WS-01", "is_demo": true},
      {"event_id": "EVT-DEMO-03", "event_type": "AUTH_FAILURE", "user": "victim.user", "host": "WS-01", "is_demo": true},
      {"event_id": "EVT-DEMO-04", "event_type": "AUTH_SUCCESS", "user": "victim.user", "host": "WS-01", "is_demo": true}
    ]"""
    res = TelemetryService.parse_and_ingest(demo_json, "test.json", db, is_demo=True, dataset_source="demo")
    assert res.valid_count == 4

    # 4. Verify DEMO vs LIVE Isolation
    live_query = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == False).all()
    demo_query = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == True).all()

    print(f"LIVE events count: {len(live_query)} (Expected: 1)")
    print(f"DEMO events count: {len(demo_query)} (Expected: 4)")
    assert len(live_query) == 1
    assert live_query[0].id == "EVT-LIVE-AUDIT-99"
    assert len(demo_query) == 4
    for ev in demo_query:
        assert ev.is_demo is True

    # 5. Run rule detection on LIVE vs DEMO
    live_alerts = RuleDetectionEngine.run_detection(db, is_demo=False)
    demo_alerts = RuleDetectionEngine.run_detection(db, is_demo=True)
    print(f"LIVE alerts generated: {len(live_alerts)} | DEMO alerts: {len(demo_alerts)}")
    assert len(demo_alerts) >= 1
    for a in demo_alerts:
        assert a.is_demo is True

    # 6. Test Idempotent Scenario Reloading (no alert duplication)
    demo_alerts_again = RuleDetectionEngine.run_detection(db, is_demo=True)
    print(f"DEMO alerts on second run (idempotency check): {len(demo_alerts_again)}")
    assert len(demo_alerts_again) == len(demo_alerts), "Duplicate alerts were created on re-detection!"

    # 7. Test Reset Demo Data (verify live record survives)
    print("Testing selective reset_demo_data()...")
    reset_demo_data(db)

    live_after_reset = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == False).all()
    demo_after_reset = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == True).all()

    print(f"LIVE events after reset: {len(live_after_reset)} (Must still be 1)")
    print(f"DEMO events after reset: {len(demo_after_reset)} (Must be 0)")
    assert len(live_after_reset) == 1
    assert live_after_reset[0].id == "EVT-LIVE-AUDIT-99"
    assert len(demo_after_reset) == 0

    # 8. Check persistence across new session
    db.close()
    db2 = SessionLocal()
    live_check = db2.query(TelemetryEvent).filter(TelemetryEvent.id == "EVT-LIVE-AUDIT-99").first()
    assert live_check is not None
    print("Disk persistence verified across sessions.")
    db2.close()

    print("Database Verification: 100% PASSED!")

if __name__ == "__main__":
    test_db_isolation()
