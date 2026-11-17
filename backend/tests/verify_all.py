import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal, Base, engine
from app.models.telemetry import TelemetryEvent
from app.models.alert import Alert
from app.models.investigation import Investigation
from app.services.ingestion.telemetry_service import TelemetryService
from app.services.detection.rule_engine import RuleDetectionEngine
from app.services.detection.isolation_forest_engine import IsolationForestEngine
from app.services.agentic.graph import execute_investigation_workflow
from app.services.evidence.evidence_graph_service import EvidenceGraphService
from app.services.response.response_service import ResponseService
from app.services.reporting.pdf_generator import PDFReportGenerator
from app.services.llm.llm_client import LLMService

def run_all_tests():
    print("=" * 60)
    print("CYBERSLEUTH AUTOMATED FORENSIC SUITE VERIFICATION")
    print("=" * 60)

    # 1. DB Init
    print("[1/10] Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    print("       Database connected successfully.")

    # 2. LLM Diagnostics
    print("[2/10] Testing LLM Provider & Degraded Fallback Diagnostics...")
    health = LLMService.check_health()
    print(f"       LLM Status: {health['status']} | Provider: {health['provider']} | Degraded: {not health['available']}")
    assert "status" in health

    # 3. Test Ingest Demo Scenarios
    print("[3/10] Loading 4 Synthetic Demo Scenarios...")
    demo_dir = Path(__file__).resolve().parent.parent.parent / "datasets" / "demo"
    scenarios = ["credential_compromise.json", "suspicious_powershell.json", "command_and_control.json", "dns_tunnelling.json"]
    
    total_loaded = 0
    for sc in scenarios:
        fpath = demo_dir / sc
        assert fpath.exists(), f"File {sc} missing"
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        res = TelemetryService.parse_and_ingest(content, sc, db, is_demo=True, dataset_source=sc)
        print(f"       Loaded {sc}: {res.valid_count} valid events.")
        total_loaded += res.valid_count
    assert total_loaded > 15, "Expected at least 15 events across scenarios"

    # 4. Rule-based detection
    print("[4/10] Testing Rule-Based Threat Detection Engine...")
    rule_alerts = RuleDetectionEngine.run_detection(db, is_demo=True)
    print(f"       Generated {len(rule_alerts)} rule-based alerts.")
    assert len(rule_alerts) >= 3, "Expected at least 3 rule-based alerts"
    for alt in rule_alerts[:3]:
        print(f"       -> [{alt.severity}] {alt.title} (Rule: {alt.rule_name})")

    # 5. Isolation Forest Unsupervised ML Detection
    print("[5/10] Testing Scikit-Learn Isolation Forest Anomaly Detection...")
    ml_alerts = IsolationForestEngine.run_detection(db, is_demo=True)
    print(f"       Detected {len(ml_alerts)} behavioral anomalies with Isolation Forest.")
    assert len(ml_alerts) >= 1, "Expected at least 1 Isolation Forest anomaly"
    sample_ml = ml_alerts[0]
    print(f"       -> Sample Anomaly: {sample_ml.title} (Score: {sample_ml.anomaly_score})")

    # 6. LangGraph StateGraph Workflow Execution
    print("[6/10] Testing LangGraph Multi-Stage Investigation Workflow...")
    primary_alert = rule_alerts[0]
    inv_id = "INV-TEST-001"
    
    # Create investigation record
    inv = Investigation(
        id=inv_id,
        alert_id=primary_alert.id,
        status="INITIALIZING",
        current_stage="alert_intake",
        progress=0,
        is_demo=True
    )
    db.merge(inv)
    db.commit()

    # Invoke compiled StateGraph
    final_state = execute_investigation_workflow(inv_id, primary_alert.id, is_demo=True)
    print(f"       LangGraph Workflow Execution Complete: {final_state['status']}")
    print(f"       Current Stage: {final_state['current_stage']} | Progress: {final_state['progress']}%")
    print(f"       Structured Findings Generated: {len(final_state['findings'])}")
    print(f"       MITRE ATT&CK Techniques Mapped: {len(final_state['mitre_mappings'])}")
    assert final_state['status'] == "COMPLETED"
    assert len(final_state['findings']) >= 2
    assert len(final_state['mitre_mappings']) >= 1

    # 7. Evidence Graph Topography
    print("[7/10] Testing Evidence Correlation Graph Construction...")
    graph = EvidenceGraphService.get_investigation_graph(inv_id, db)
    print(f"       Graph Constructed: {len(graph.nodes)} nodes, {len(graph.edges)} edges.")
    print(f"       Observed edges: {graph.stats['observed_count']} | Inferred edges: {graph.stats['inferred_count']}")
    assert len(graph.nodes) >= 3
    assert len(graph.edges) >= 2

    # 8. Human-in-the-Loop Simulated Response Execution
    print("[8/10] Testing Human Approval of Simulated Response Actions...")
    from app.models.response import ResponseAction
    actions = db.query(ResponseAction).filter(ResponseAction.investigation_id == inv_id).all()
    assert len(actions) >= 1, "Expected staged response actions"
    sample_act = actions[0]
    sample_act.status = "PENDING_APPROVAL"
    db.commit()
    print(f"       Staged Action: {sample_act.action_type} on {sample_act.target_entity} (Status: {sample_act.status})")
    
    # Approve action
    appr = ResponseService.approve_action(sample_act.id, "lead_analyst_alice", "Simulated containment verified.", db)
    print(f"       Approved Action: {appr.id} -> Status: {appr.status} (Simulated: {appr.is_simulated})")
    assert appr.status == "EXECUTED"
    assert "SIMULATION" in appr.execution_log

    # 9. ReportLab PDF Report Generation
    print("[9/10] Testing Real ReportLab PDF Generation...")
    pdf_bytes = PDFReportGenerator.generate_investigation_report(inv_id, db)
    print(f"       Generated PDF Report: {len(pdf_bytes)} bytes.")
    assert pdf_bytes.startswith(b"%PDF"), "Generated output is not a valid PDF file"
    assert len(pdf_bytes) > 2000, "PDF file size too small"

    # 10. Verification of Partition Isolation
    print("[10/10] Verifying Partition Separation (DEMO vs LIVE)...")
    live_events_count = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == False).count()
    demo_events_count = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == True).count()
    print(f"        LIVE partition: {live_events_count} records | DEMO partition: {demo_events_count} records.")
    assert demo_events_count == total_loaded
    assert live_events_count == 0, "No synthetic records leaked into LIVE partition"

    db.close()
    print("=" * 60)
    print("ALL 10 FORENSIC ENGINE VERIFICATION CHECKS PASSED PERFECTLY!")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()
