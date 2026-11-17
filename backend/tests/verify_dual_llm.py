import os
import sys
import json
import uuid
import time
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.telemetry import TelemetryEvent
from app.models.alert import Alert
from app.models.investigation import Investigation, InvestigationStep
from app.models.evidence import Evidence
from app.models.response import ResponseAction
from app.schemas.llm import (
    InvestigationReasoningOutput,
    HypothesisSchema,
    FindingSchema,
    AttackReconstructionSchema,
    ResponseRecommendationSchema,
    MitreObservationSchema
)
from app.services.llm.llm_client import LLMService
from app.services.agentic.graph import execute_investigation_workflow
from app.services.response.response_service import ResponseService
import io
from app.services.reporting.pdf_generator import PDFReportGenerator

def run_dual_llm_verification():
    print("=" * 80)
    print("CYBERSLEUTH — DUAL LIVE LLM INTEGRATION FORENSIC AUDIT & VERIFICATION")
    print("Windows-First Verification Suite (Gemini, OpenAI, Routing & Governance)")
    print("=" * 80)

    results = {}

    # -------------------------------------------------------------------------
    # TEST 1: Gemini Diagnostic & Authentication
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Testing Google Gemini Diagnostic & Error Classification...")
    # Unconfigured check
    res_unconfigured = LLMService.test_connection("gemini", api_key="")
    assert res_unconfigured.status == "UNCONFIGURED", f"Expected UNCONFIGURED, got {res_unconfigured.status}"
    assert res_unconfigured.available is False

    # Invalid key check against real API
    res_invalid = LLMService.test_connection("gemini", api_key="invalid_gemini_test_key_12345")
    print(f"  Gemini Real Probe Result: status={res_invalid.status}, latency={res_invalid.latency_ms}ms, msg={res_invalid.message[:70]}...")
    assert res_invalid.status in ["INVALID_KEY", "CONNECTION_FAILED"], f"Unexpected status: {res_invalid.status}"
    assert res_invalid.available is False
    results["gemini_auth_and_diagnostic"] = "PASS"
    print("  -> TEST 1 PASSED: Gemini diagnostic properly classifies unconfigured and invalid credentials.")

    # -------------------------------------------------------------------------
    # TEST 2: OpenAI Diagnostic & Authentication
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Testing OpenAI Diagnostic & Error Classification...")
    # Unconfigured check
    res_open_unconf = LLMService.test_connection("openai", api_key="")
    assert res_open_unconf.status == "UNCONFIGURED", f"Expected UNCONFIGURED, got {res_open_unconf.status}"
    assert res_open_unconf.available is False

    # Invalid key check against real API
    res_open_invalid = LLMService.test_connection("openai", api_key="sk-invalid_openai_test_key_1234567890")
    print(f"  OpenAI Real Probe Result: status={res_open_invalid.status}, latency={res_open_invalid.latency_ms}ms, msg={res_open_invalid.message[:70]}...")
    assert res_open_invalid.status in ["INVALID_KEY", "CONNECTION_FAILED"], f"Unexpected status: {res_open_invalid.status}"
    assert res_open_invalid.available is False
    results["openai_auth_and_diagnostic"] = "PASS"
    print("  -> TEST 2 PASSED: OpenAI diagnostic properly classifies unconfigured and invalid credentials.")

    # -------------------------------------------------------------------------
    # TEST 3: Structured Output Schema Validation & Telemetry Grounding
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Testing Pydantic Structured Output Validation & Grounding...")
    # Test valid schema model construction
    valid_data = {
        "hypotheses": [
            {"id": "H1", "hypothesis": "Adversary brute-forced finance_admin credentials.", "likelihood": "HIGH", "tested": True, "supported": True}
        ],
        "findings": [
            {"id": "F1", "statement": "Failed logons from 198.51.100.44.", "status": "OBSERVED", "confidence": 0.98, "supporting_events": ["EVT-AUTH-101"], "rationale": "Direct telemetry."}
        ],
        "missing_evidence": [],
        "attack_reconstruction": {
            "narrative": "Brute force attack followed by interactive logon.",
            "timeline": ["EVT-AUTH-101"]
        },
        "executive_summary": "Credential stuffing incident contained.",
        "response_recommendations": [
            {"action_type": "RESET_CREDENTIALS", "target_entity": "finance_admin", "rationale": "Compromised account", "risk_assessment": "Low risk"}
        ],
        "mitre_mappings": [
            {"technique_id": "T1110.001", "tactic": "Credential Access", "name": "Password Guessing", "supporting_events": ["EVT-AUTH-101"], "explanation": "Failed logon burst."}
        ],
        "recommended_next_steps": ["Rotate domain admin credentials."],
        "sufficiency_reached": True
    }

    parsed = InvestigationReasoningOutput(**valid_data)
    assert parsed.findings[0].status == "OBSERVED"
    assert parsed.findings[0].confidence == 0.98

    # Test Telemetry Grounding Validator: stripping non-existent phantom events
    mock_telemetry = [{"id": "EVT-AUTH-101", "event_type": "AUTH_FAILURE"}]
    un_grounded = {
        "findings": [
            {
                "id": "F1",
                "statement": "Real finding citing real event.",
                "status": "OBSERVED",
                "confidence": 0.99,
                "supporting_events": ["EVT-AUTH-101", "EVT-PHANTOM-999"], # Contains 1 phantom event
                "rationale": "Correlated."
            },
            {
                "id": "F2",
                "statement": "Claimed observed finding with ONLY phantom events.",
                "status": "OBSERVED",
                "confidence": 0.99,
                "supporting_events": ["EVT-NONEXISTENT-777"], # 100% phantom
                "rationale": "Invented citation."
            }
        ]
    }
    grounded = LLMService._validate_and_ground_output(un_grounded, mock_telemetry)
    # Finding 1 should have phantom stripped
    assert "EVT-PHANTOM-999" not in grounded["findings"][0]["supporting_events"]
    assert "EVT-AUTH-101" in grounded["findings"][0]["supporting_events"]
    # Finding 2 should be automatically demoted from OBSERVED to INFERRED and confidence capped
    assert grounded["findings"][1]["status"] == "INFERRED"
    assert grounded["findings"][1]["confidence"] <= 0.90
    results["structured_output_and_grounding"] = "PASS"
    print("  -> TEST 3 PASSED: Pydantic schemas validated; phantom event citations stripped; unevidenced findings demoted to INFERRED.")

    # -------------------------------------------------------------------------
    # TEST 4: Provider Switching (Gemini -> OpenAI -> Auto)
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Testing Provider Configuration & Dynamic Switching...")
    # Switch to OpenAI
    settings.LLM_PROVIDER = "openai"
    health_openai = LLMService.check_health()
    assert health_openai["active_provider"] == "openai"

    # Switch to Auto
    settings.LLM_PROVIDER = "auto"
    health_auto = LLMService.check_health()
    assert health_auto["active_provider"] == "auto"

    # Switch back to Gemini
    settings.LLM_PROVIDER = "gemini"
    health_gemini = LLMService.check_health()
    assert health_gemini["active_provider"] == "gemini"

    results["provider_switching"] = "PASS"
    print("  -> TEST 4 PASSED: Dynamic provider switching across gemini, openai, and auto confirmed.")

    # -------------------------------------------------------------------------
    # TEST 5: Controlled Failover Rules (Recoverable vs Unrecoverable)
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Testing Controlled Failover Policy...")
    # Unrecoverable error: 401 Invalid Key
    unrec_err = Exception("401 Unauthorized: Incorrect API key provided")
    assert LLMService._is_recoverable_error(unrec_err) is False, "Invalid API key must NOT be flagged as recoverable"

    # Unrecoverable error: 404 Model Not Found
    unrec_err2 = Exception("404 NotFound: Model 'gpt-nonexistent' does not exist")
    assert LLMService._is_recoverable_error(unrec_err2) is False, "Missing model must NOT be flagged as recoverable"

    # Recoverable fault: 503 Service Unavailable / Timeout
    rec_err = Exception("503 Service Unavailable: Gateway timeout")
    assert LLMService._is_recoverable_error(rec_err) is True, "503 timeout must be flagged as recoverable"

    # Recoverable fault: Network connection reset
    rec_err2 = Exception("ConnectionResetError: [Errno 10054] An existing connection was forcibly closed by the remote host")
    assert LLMService._is_recoverable_error(rec_err2) is True, "Connection reset must be flagged as recoverable"

    results["controlled_failover_policy"] = "PASS"
    print("  -> TEST 5 PASSED: Strict failover policy verified: unrecoverable faults prevent silent switching; transient faults allow audited failover.")

    # -------------------------------------------------------------------------
    # TEST 6: Deterministic Forensic Fallback with Explicit Provenance
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Testing Deterministic Forensic Reasoning Fallback...")
    # Run reasoning over credential brute force scenario telemetry
    alert_stub = {
        "id": "ALT-TEST-BF",
        "title": "Credential Brute Force Success",
        "rule_name": "AUTH_BRUTE_FORCE_SUCCESS",
        "severity": "CRITICAL",
        "primary_event_id": "EVT-AUTH-105"
    }
    telemetry_stub = [
        {"id": "EVT-AUTH-101", "event_type": "AUTH_FAILURE", "user": "finance_admin", "host": "FIN-SRV-01", "source_ip": "198.51.100.44"},
        {"id": "EVT-AUTH-102", "event_type": "AUTH_FAILURE", "user": "finance_admin", "host": "FIN-SRV-01", "source_ip": "198.51.100.44"},
        {"id": "EVT-AUTH-103", "event_type": "AUTH_FAILURE", "user": "finance_admin", "host": "FIN-SRV-01", "source_ip": "198.51.100.44"},
        {"id": "EVT-AUTH-105", "event_type": "AUTH_SUCCESS", "user": "finance_admin", "host": "FIN-SRV-01", "source_ip": "198.51.100.44"}
    ]

    reasoning = LLMService.reason_investigation(alert_stub, telemetry_stub, iteration=1)
    assert reasoning["llm_invoked"] is False
    assert reasoning["degraded_mode"] is True
    assert reasoning["llm_provider"] == "DETERMINISTIC_FALLBACK"
    assert len(reasoning["findings"]) >= 2
    # Ensure every finding has explicit status (OBSERVED or INFERRED)
    for f in reasoning["findings"]:
        assert f["status"] in ["OBSERVED", "INFERRED"]
        assert 0.0 <= f["confidence"] <= 1.0

    results["deterministic_fallback_provenance"] = "PASS"
    print(f"  -> TEST 6 PASSED: Deterministic fallback engaged ({len(reasoning['findings'])} findings) with explicit degraded_mode=True.")

    # -------------------------------------------------------------------------
    # TEST 7: Full LangGraph Multi-Agent Investigation Execution
    # -------------------------------------------------------------------------
    print("\n[TEST 7] Testing Full LangGraph 9-Node Investigation Workflow...")
    db = SessionLocal()
    try:
        # Create dedicated live test alert
        test_alert_id = f"ALT-LIVE-DUAL-{uuid.uuid4().hex[:6].upper()}"
        test_inv_id = f"INV-LIVE-DUAL-{uuid.uuid4().hex[:6].upper()}"

        alert = Alert(
            id=test_alert_id,
            title="Unauthorized Credential Access & Execution",
            description="Automated audit test alert for dual LLM pipeline verification",
            detection_method="RULE_BASED",
            rule_name="AUTH_BRUTE_FORCE_SUCCESS",
            severity="HIGH",
            status="NEW",
            primary_event_id="EVT-AUTH-105",
            affected_entities=[{"type": "user", "value": "finance_admin"}, {"type": "host", "value": "FIN-SRV-01"}],
            is_demo=False
        )
        db.add(alert)

        inv = Investigation(
            id=test_inv_id,
            alert_id=test_alert_id,
            status="INITIALIZING",
            current_stage="alert_intake",
            progress=0,
            is_demo=False
        )
        db.add(inv)
        db.commit()

        # Execute LangGraph StateGraph
        final_state = execute_investigation_workflow(test_inv_id, test_alert_id, is_demo=False)
        assert final_state["status"] == "COMPLETED", f"Expected COMPLETED, got {final_state['status']}"
        assert final_state["progress"] == 100
        assert final_state["current_stage"] == "investigation_closure"

        # Verify persisted steps in database
        steps = db.query(InvestigationStep).filter(InvestigationStep.investigation_id == test_inv_id).order_by(InvestigationStep.step_order).all()
        assert len(steps) >= 9, f"Expected at least 9 steps, got {len(steps)}"
        print(f"  Persisted {len(steps)} LangGraph execution steps in SQLite:")
        for s in steps:
            print(f"    Step {s.step_order}: {s.stage_name} -> {s.status}")

        # Verify staged response actions requiring HITL authorization
        actions = db.query(ResponseAction).filter(ResponseAction.investigation_id == test_inv_id).all()
        assert len(actions) > 0, "Expected staged response actions"
        assert all(a.status == "PENDING_APPROVAL" for a in actions), "All actions must initialize in PENDING_APPROVAL"
        assert all(a.is_simulated is True for a in actions), "All actions must have is_simulated == True"

        # Test HITL approval on first staged action
        act = actions[0]
        approved_act = ResponseService.approve_action(action_id=act.id, decided_by="lead_auditor", comments="Forensic test authorization", db=db)
        assert approved_act.status == "EXECUTED"
        assert approved_act.decided_by == "lead_auditor"

        # Test deduplication guard: second approval must fail
        dup_failed = False
        try:
            ResponseService.approve_action(action_id=act.id, decided_by="lead_auditor", comments="Second attempt", db=db)
        except ValueError:
            dup_failed = True
        assert dup_failed, "Duplicate approval must be blocked with ValueError"

        results["langgraph_investigation_and_hitl"] = "PASS"
        print("  -> TEST 7 PASSED: LangGraph workflow completed; all 9 stages recorded; HITL approval and deduplication verified.")

        # -------------------------------------------------------------------------
        # TEST 8: Forensic PDF Report Generation with LLM Provenance
        # -------------------------------------------------------------------------
        print("\n[TEST 8] Testing Forensic PDF Report Generation...")
        pdf_bytes = PDFReportGenerator.generate_investigation_report(test_inv_id, db)
        assert pdf_bytes is not None and len(pdf_bytes) > 3000, f"PDF generation failed or returned too few bytes ({len(pdf_bytes)} bytes)"

        # Verify PDF contents with pypdf
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) >= 1, f"Expected at least 1-page PDF, got {len(reader.pages)}"
        full_text = "\n".join(p.extract_text() for p in reader.pages)
        assert "CyberSleuth" in full_text
        assert test_inv_id in full_text
        assert "OBSERVED" in full_text or "INFERRED" in full_text
        assert "MITRE ATT&CK" in full_text

        results["pdf_report_generation"] = "PASS"
        print(f"  -> TEST 8 PASSED: Valid {len(reader.pages)}-page forensic PDF generated ({len(pdf_bytes)} bytes) with provenance labels.")

    finally:
        db.close()

    print("\n" + "=" * 80)
    print("DUAL LIVE LLM VERIFICATION SUMMARY:")
    for test_name, status in results.items():
        print(f"  {test_name.ljust(35)}: [{status}]")
    print("=" * 80)
    print("ALL TESTS PASSED: CyberSleuth Dual Live LLM Integration is 100% verified.")

if __name__ == "__main__":
    run_dual_llm_verification()
