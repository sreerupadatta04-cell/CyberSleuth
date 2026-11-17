import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.telemetry import TelemetryEvent
from app.models.alert import Alert
from app.services.ingestion.telemetry_service import TelemetryService
from app.services.detection.rule_engine import RuleDetectionEngine
from app.services.detection.isolation_forest_engine import IsolationForestEngine
from app.api.routes.settings import reset_demo_data

def test_detection_engine():
    db = SessionLocal()
    reset_demo_data(db)

    demo_dir = Path(__file__).resolve().parent.parent.parent / "datasets" / "demo"

    # --- PART 1: TEST RULE DETECTION ON ALL 4 SCENARIOS ---
    expected_rules = {
        "credential_compromise.json": ["AUTH_BRUTE_FORCE_SUCCESS", "RECONNAISSANCE_COMMAND_EXECUTED"],
        "suspicious_powershell.json": ["SUSPICIOUS_POWERSHELL_EXECUTION", "OFFICE_SPAWNED_SHELL"],
        "command_and_control.json": ["C2_BEACONING_PATTERN"],
        "dns_tunnelling.json": ["DNS_TUNNELING_EXFILTRATION"]
    }

    all_rule_names = set()
    for filename, rules in expected_rules.items():
        with open(demo_dir / filename, "r", encoding="utf-8") as f:
            content = f.read()
        res = TelemetryService.parse_and_ingest(content, filename, db, is_demo=True, dataset_source=filename)
        assert res.valid_count > 0

        alerts = RuleDetectionEngine.run_detection(db, is_demo=True)
        detected_rules = {a.rule_name for a in alerts if a.rule_name}
        all_rule_names.update(detected_rules)
        for r in rules:
            assert r in detected_rules, f"Expected rule {r} for {filename} not triggered!"
        print(f"Scenario {filename}: Successfully triggered {rules}")

    # Verify event references are valid
    all_events = {e.id for e in db.query(TelemetryEvent).all()}
    for a in db.query(Alert).filter(Alert.detection_method == "RULE_BASED").all():
        if a.primary_event_id:
            assert a.primary_event_id in all_events, f"Alert {a.id} references non-existent event {a.primary_event_id}"

    # --- PART 2: TEST ISOLATION FOREST ---
    print("\nTesting Scikit-Learn Isolation Forest Engine...")
    
    # 1. Test missing-value handling
    missing_val_event = TelemetryEvent(
        id="EVT-NULL-TEST",
        event_type="NETWORK_CONNECT",
        severity="INFO",
        user=None, # Missing user
        host=None, # Missing host
        source_port=None,
        destination_port=None, # Missing port
        command_line=None, # Missing command line
        domain=None, # Missing domain
        is_demo=True
    )
    features = IsolationForestEngine._extract_features(missing_val_event)
    print(f"Extracted features for missing-value record: {features}")
    assert len(features) == 7
    assert all(isinstance(v, (int, float)) for v in features)
    assert not any(v is None for v in features)

    # 2. Run detection across ingested events
    ml_alerts = IsolationForestEngine.run_detection(db, is_demo=True, contamination=0.15)
    print(f"Isolation Forest anomalies flagged: {len(ml_alerts)}")
    assert len(ml_alerts) >= 1

    for a in ml_alerts:
        assert a.detection_method == "ISOLATION_FOREST"
        assert 0.0 <= a.anomaly_score <= 1.0, f"Invalid anomaly score: {a.anomaly_score}"
        assert a.primary_event_id in all_events
        # Check disclaimer statement
        assert "not automatically malicious" in a.explanation.lower(), "Missing non-malicious disclaimer in IF alert"

    print("Detection Engine Verification: 100% PASSED!")
    db.close()

if __name__ == "__main__":
    test_detection_engine()
