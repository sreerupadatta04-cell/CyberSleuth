import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.services.ingestion.telemetry_service import TelemetryService
from app.services.detection.rule_engine import RuleDetectionEngine
from app.services.detection.isolation_forest_engine import IsolationForestEngine
from app.models.alert import Alert
from app.models.telemetry import TelemetryEvent
from app.models.investigation import Investigation, InvestigationStep
from app.models.evidence import Evidence, EvidenceRelationship
from app.models.response import ResponseAction, ApprovalHistory

router = APIRouter()

DEMO_DIR = settings.BASE_DIR.parent / "datasets" / "demo"

SCENARIOS = {
    "credential_compromise": {
        "id": "credential_compromise",
        "title": "Scenario 1: Credential Compromise & Brute Force",
        "category": "Credential Access / Privilege Escalation",
        "severity": "HIGH",
        "description": "Repeated authentication failures against account 'a.martinez', followed by suspicious successful login, discovery reconnaissance (whoami /priv), and SMB admin share probing.",
        "mitre_techniques": ["T1110 (Brute Force)", "T1078 (Valid Accounts)", "T1087 (Account Discovery)", "T1021.002 (SMB Shares)"],
        "filename": "credential_compromise.json"
    },
    "suspicious_powershell": {
        "id": "suspicious_powershell",
        "title": "Scenario 2: Malicious PowerShell Download Cradle",
        "category": "Execution / Defense Evasion",
        "severity": "CRITICAL",
        "description": "Office document WINWORD.EXE launches obfuscated PowerShell with -NoP -Exec Bypass -EncodedCommand to fetch an external payload and write local persistence.",
        "mitre_techniques": ["T1204.002 (Malicious File)", "T1059.001 (PowerShell)", "T1547.001 (Persistence Script)"],
        "filename": "suspicious_powershell.json"
    },
    "command_and_control": {
        "id": "command_and_control",
        "title": "Scenario 3: Command & Control (C2) Beaconing",
        "category": "Command and Control",
        "severity": "CRITICAL",
        "description": "Recurring periodic outbound HTTPS socket connections from internal workstation WS-DEV-02 to external IP 185.220.101.5 exhibiting beaconing jitter.",
        "mitre_techniques": ["T1071.001 (Web Protocols)", "T1573 (Encrypted Channel)"],
        "filename": "command_and_control.json"
    },
    "dns_tunnelling": {
        "id": "dns_tunnelling",
        "title": "Scenario 4: DNS Tunneling & Data Exfiltration",
        "category": "Exfiltration / Covert Channel",
        "severity": "CRITICAL",
        "description": "Series of high-entropy, long-string DNS queries to apex domain 'exfil-dns.net' used to covertly exfiltrate sensitive internal records.",
        "mitre_techniques": ["T1071.004 (DNS Communication)", "T1048 (Exfiltration Over Alternative Protocol)"],
        "filename": "dns_tunnelling.json"
    }
}

@router.get("")
def list_scenarios():
    scenario_list = []
    for sc_id, sc in SCENARIOS.items():
        # Read preview events from dataset file
        file_path = DEMO_DIR / sc["filename"]
        preview = []
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    preview = data[:3]
            except Exception:
                pass
        
        scenario_list.append({
            **sc,
            "preview_events": preview
        })
    return scenario_list

@router.post("/{scenario_id}/load")
def load_scenario(
    scenario_id: str,
    reset_first: bool = Query(False),
    freshen_timestamps: bool = Query(True),
    db: Session = Depends(get_db)
):
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario '{scenario_id}' not found.")

    sc = SCENARIOS[scenario_id]
    file_path = DEMO_DIR / sc["filename"]
    if not file_path.exists():
        raise HTTPException(status_code=500, detail=f"Scenario dataset file {sc['filename']} not found.")

    # 1. Optionally reset existing demo partition for pristine scenario isolation
    if reset_first:
        db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == True).delete()
        db.query(Alert).filter(Alert.is_demo == True).delete()
        demo_invs = db.query(Investigation).filter(Investigation.is_demo == True).all()
        for inv in demo_invs:
            db.query(InvestigationStep).filter(InvestigationStep.investigation_id == inv.id).delete()
            db.query(Evidence).filter(Evidence.investigation_id == inv.id).delete()
            db.query(EvidenceRelationship).filter(EvidenceRelationship.investigation_id == inv.id).delete()
            db.query(ResponseAction).filter(ResponseAction.investigation_id == inv.id).delete()
            db.query(ApprovalHistory).filter(ApprovalHistory.investigation_id == inv.id).delete()
            db.delete(inv)
        db.commit()

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 2. Freshen timestamps to current time so newly loaded scenario events appear at top of feeds
    events_raw = json.loads(content)
    scenario_event_ids = [e.get("event_id") or e.get("id") for e in events_raw if e.get("event_id") or e.get("id")]

    if freshen_timestamps and isinstance(events_raw, list):
        now = datetime.utcnow()
        total_evts = len(events_raw)
        for i, ev in enumerate(events_raw):
            offset_seconds = (total_evts - 1 - i) * 15
            ev["timestamp"] = (now - timedelta(seconds=offset_seconds)).isoformat() + "Z"
        content = json.dumps(events_raw)

    # 3. Ingest with strict is_demo=True
    ingest_res = TelemetryService.parse_and_ingest(
        content=content,
        filename=sc["filename"],
        db=db,
        is_demo=True,
        dataset_source=f"demo:{scenario_id}"
    )

    # 4. Automatically run detection engines on the newly loaded demo telemetry
    rule_alerts = RuleDetectionEngine.run_detection(db, is_demo=True)
    ml_alerts = IsolationForestEngine.run_detection(db, is_demo=True)

    # 5. Precisely identify the primary alert corresponding to THIS scenario
    SCENARIO_PRIMARY_MAP = {
        "credential_compromise": ("AUTH_BRUTE_FORCE_SUCCESS", "EVT-CC-106"),
        "suspicious_powershell": ("SUSPICIOUS_POWERSHELL_EXECUTION", "EVT-PS-202"),
        "command_and_control": ("C2_BEACONING", "EVT-C2-305"),
        "dns_tunnelling": ("DNS_TUNNELING_EXFILTRATION", "EVT-DNS-405"),
    }

    expected_rule, expected_evt = SCENARIO_PRIMARY_MAP.get(scenario_id, ("", ""))

    # Fetch alerts whose primary event is in this scenario's event set
    scenario_alerts = (
        db.query(Alert)
        .filter(Alert.is_demo == True, Alert.primary_event_id.in_(scenario_event_ids))
        .all()
    )

    # Sort alerts so expected primary alert comes first, followed by CRITICAL/HIGH
    def alert_priority(a: Alert):
        if expected_rule and a.rule_name == expected_rule:
            return 0
        if expected_evt and a.primary_event_id == expected_evt:
            return 1
        if a.severity == "CRITICAL":
            return 2
        if a.severity == "HIGH":
            return 3
        if a.severity == "MEDIUM":
            return 4
        return 5

    scenario_alerts.sort(key=alert_priority)

    # Fallback to general demo alerts if no scenario-specific alert
    if not scenario_alerts:
        scenario_alerts = db.query(Alert).filter(Alert.is_demo == True).order_by(Alert.created_at.desc()).all()

    primary_alert_id = scenario_alerts[0].id if scenario_alerts else None
    primary_alert_title = scenario_alerts[0].title if scenario_alerts else "No Alert Generated"

    return {
        "message": f"Successfully loaded '{sc['title']}' demo telemetry into isolated DEMO partition.",
        "scenario_id": scenario_id,
        "events_ingested": ingest_res.valid_count,
        "rule_alerts_generated": len(rule_alerts),
        "ml_anomalies_detected": len(ml_alerts),
        "primary_alert_id": primary_alert_id,
        "primary_alert_title": primary_alert_title,
        "alerts": [
            {
                "id": a.id,
                "title": a.title,
                "severity": a.severity,
                "detection_method": a.detection_method,
                "primary_event_id": a.primary_event_id
            }
            for a in scenario_alerts[:10]
        ]
    }
