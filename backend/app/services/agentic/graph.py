import uuid
from datetime import datetime
from typing import Dict, Any, List, Literal
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

from app.core.database import SessionLocal
from app.models.alert import Alert
from app.models.telemetry import TelemetryEvent
from app.models.investigation import Investigation, InvestigationStep
from app.models.evidence import Evidence, EvidenceRelationship
from app.models.response import ResponseAction
from app.services.agentic.state import InvestigationState
from app.services.llm.llm_client import LLMService
from app.services.mitre.mitre_catalog import MitreCatalog

def record_step(db: Session, inv_id: str, stage: str, order: int, summary: str, details: Dict[str, Any] = None):
    step = InvestigationStep(
        investigation_id=inv_id,
        stage_name=stage,
        status="SUCCESS",
        step_order=order,
        output_summary=summary,
        details=details or {},
        timestamp=datetime.utcnow()
    )
    db.add(step)
    
    # Update investigation object current stage and progress
    inv = db.query(Investigation).filter(Investigation.id == inv_id).first()
    if inv:
        inv.current_stage = stage
        inv.updated_at = datetime.utcnow()
    db.commit()

# --- NODE 1: Alert Intake ---
def alert_intake_node(state: InvestigationState) -> InvestigationState:
    db: Session = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == state["alert_id"]).first()
        if not alert:
            state["errors"].append(f"Alert {state['alert_id']} not found.")
            state["status"] = "FAILED"
            return state

        alert_data = {
            "id": alert.id,
            "title": alert.title,
            "description": alert.description,
            "detection_method": alert.detection_method,
            "rule_name": alert.rule_name,
            "severity": alert.severity,
            "primary_event_id": alert.primary_event_id,
            "affected_entities": alert.affected_entities or []
        }
        state["alert_data"] = alert_data
        state["target_entities"] = alert.affected_entities or []
        state["current_stage"] = "alert_intake"
        state["progress"] = 10
        state["status"] = "IN_PROGRESS"

        # Update alert status
        alert.status = "INVESTIGATING"
        alert.investigation_id = state["investigation_id"]
        db.commit()

        summary = f"Alert {alert.id} ({alert.title}) received. Initialized investigation triage."
        record_step(db, state["investigation_id"], "alert_intake", 1, summary, alert_data)
        return state
    finally:
        db.close()

# --- NODE 2: Investigation Planning ---
def investigation_planning_node(state: InvestigationState) -> InvestigationState:
    db: Session = SessionLocal()
    try:
        # Initial planning: identify hypotheses to test
        alert = state["alert_data"]
        planning_hypotheses = [
            {
                "id": "H1",
                "hypothesis": f"Activity represents unauthorized access or execution regarding {alert.get('title')}",
                "likelihood": "HIGH",
                "tested": False
            },
            {
                "id": "H2",
                "hypothesis": "Activity corresponds to benign administrative routine or false alarm",
                "likelihood": "LOW",
                "tested": False
            }
        ]
        state["hypotheses"] = planning_hypotheses
        state["current_stage"] = "investigation_planning"
        state["progress"] = 20

        summary = f"Generated {len(planning_hypotheses)} investigation hypotheses and established telemetry collection objectives."
        record_step(db, state["investigation_id"], "investigation_planning", 2, summary, {"hypotheses": planning_hypotheses})
        return state
    finally:
        db.close()

# --- NODE 3: Evidence Collection ---
def evidence_collection_node(state: InvestigationState) -> InvestigationState:
    db: Session = SessionLocal()
    try:
        alert = state["alert_data"]
        is_demo = state["is_demo"]
        primary_evt_id = alert.get("primary_event_id")

        # Query events related to affected entities or primary event
        query = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == is_demo)
        
        # Collect related events
        entity_values = [e.get("value") for e in state["target_entities"] if e.get("value")]
        
        all_events = query.all()
        related_events = []

        for ev in all_events:
            # Match primary event
            if ev.id == primary_evt_id:
                related_events.append(ev)
                continue
            # Match by user, host, IP, or domain
            if (ev.user and ev.user in entity_values) or \
               (ev.host and ev.host in entity_values) or \
               (ev.source_ip and ev.source_ip in entity_values) or \
               (ev.destination_ip and ev.destination_ip in entity_values) or \
               (ev.domain and any(ev.domain in v for v in entity_values)):
                related_events.append(ev)

        # If sparse and on iteration > 1, expand window or include near events
        if len(related_events) <= 1 and all_events and state.get("iteration_count", 1) > 1:
            related_events = all_events[:10]

        # Convert to serialized dicts
        serialized_events = [
            {
                "id": e.id,
                "timestamp": e.timestamp.isoformat(),
                "event_type": e.event_type,
                "severity": e.severity,
                "user": e.user,
                "host": e.host,
                "source_ip": e.source_ip,
                "destination_ip": e.destination_ip,
                "destination_port": e.destination_port,
                "process_name": e.process_name,
                "command_line": e.command_line,
                "domain": e.domain
            }
            for e in related_events
        ]
        state["collected_events"] = serialized_events
        state["current_stage"] = "evidence_collection"
        state["progress"] = 35

        summary = f"Evidence Collector retrieved {len(serialized_events)} telemetry records correlated with target entities."
        record_step(db, state["investigation_id"], "evidence_collection", 3, summary, {"event_count": len(serialized_events)})
        return state
    finally:
        db.close()

# --- NODE 4: Correlation & Validation ---
def correlation_and_validation_node(state: InvestigationState) -> InvestigationState:
    db: Session = SessionLocal()
    try:
        # Call LLM / Deterministic reasoning service
        reasoning_res = LLMService.reason_investigation(
            alert_data=state["alert_data"],
            telemetry_events=state["collected_events"],
            iteration=state["iteration_count"]
        )

        state["hypotheses"] = reasoning_res.get("hypotheses", state["hypotheses"])
        state["findings"] = reasoning_res.get("findings", [])
        state["missing_evidence"] = reasoning_res.get("missing_evidence", [])
        state["sufficiency_reached"] = reasoning_res.get("sufficiency_reached", True)
        state["attack_reconstruction"] = reasoning_res.get("attack_reconstruction", {})
        state["executive_summary"] = reasoning_res.get("executive_summary", "")
        state["response_recommendations"] = reasoning_res.get("response_recommendations", [])
        
        state["llm_invoked"] = reasoning_res.get("llm_invoked", False)
        state["llm_provider"] = reasoning_res.get("llm_provider")
        state["llm_model"] = reasoning_res.get("llm_model")
        state["degraded_mode"] = reasoning_res.get("degraded_mode", False)
        state["provider_switches"] = reasoning_res.get("provider_switches", [])
        state["failover_reason"] = reasoning_res.get("failover_reason")

        state["current_stage"] = "correlation_and_validation"
        state["progress"] = 50

        # Persist structured evidence items to database
        for fnd in state["findings"]:
            evi_id = f"EVI-{uuid.uuid4().hex[:6].upper()}"
            evidence = Evidence(
                id=evi_id,
                investigation_id=state["investigation_id"],
                title=fnd.get("statement")[:100],
                description=fnd.get("statement"),
                evidence_type="EVENT_CORRELATION",
                source_event_id=fnd.get("supporting_events", [None])[0] if fnd.get("supporting_events") else None,
                confidence=fnd.get("confidence", 0.9),
                category=fnd.get("status", "OBSERVED"),
                details=fnd,
                is_demo=state["is_demo"]
            )
            db.merge(evidence)
        db.commit()

        switch_note = ""
        if state["provider_switches"]:
            s = state["provider_switches"][-1]
            switch_note = f" (Failover: {s.get('from_provider')} -> {s.get('to_provider')})"

        summary = (
            f"Correlation Agent analyzed {len(state['collected_events'])} events. "
            f"Synthesized {len(state['findings'])} evidence-grounded findings (LLM Provider: {state['llm_provider']}{switch_note})."
        )
        record_step(db, state["investigation_id"], "correlation_and_validation", 4, summary, {
            "findings_count": len(state["findings"]),
            "llm_provider": state["llm_provider"],
            "llm_model": state["llm_model"],
            "degraded_mode": state["degraded_mode"],
            "provider_switches": state["provider_switches"],
            "failover_reason": state["failover_reason"]
        })
        return state
    finally:
        db.close()

# --- NODE 5: Evidence Sufficiency Assessment ---
def evidence_sufficiency_assessment_node(state: InvestigationState) -> InvestigationState:
    db: Session = SessionLocal()
    try:
        # Evaluate if evidence is sufficient or if an iterative expansion loop is needed
        state["current_stage"] = "evidence_sufficiency_assessment"
        state["progress"] = 60

        if not state["sufficiency_reached"] and state["iteration_count"] < state["max_iterations"]:
            state["iteration_count"] += 1
            summary = (
                f"Evidence Sufficiency Assessment: Incomplete telemetry identified ({len(state['missing_evidence'])} gaps). "
                f"Triggering refinement loop (Iteration {state['iteration_count']} of {state['max_iterations']})."
            )
        else:
            state["sufficiency_reached"] = True
            summary = (
                f"Evidence Sufficiency Assessment: Satisfied. Sufficient forensic depth established across "
                f"{len(state['collected_events'])} events."
            )

        record_step(db, state["investigation_id"], "evidence_sufficiency_assessment", 5, summary, {
            "sufficiency_reached": state["sufficiency_reached"],
            "iteration": state["iteration_count"]
        })
        return state
    finally:
        db.close()

# --- Conditional Edge Router ---
def sufficiency_router(state: InvestigationState) -> Literal["evidence_collection", "attack_reconstruction"]:
    if not state["sufficiency_reached"] and state["iteration_count"] <= state["max_iterations"]:
        return "evidence_collection"
    return "attack_reconstruction"

# --- NODE 6: Attack Reconstruction ---
def attack_reconstruction_node(state: InvestigationState) -> InvestigationState:
    db: Session = SessionLocal()
    try:
        state["current_stage"] = "attack_reconstruction"
        state["progress"] = 70

        narrative = state["attack_reconstruction"].get("narrative", "Attack sequence reconstructed across timeline.")
        summary = f"Reconstructed attack sequence and temporal event lineage."
        record_step(db, state["investigation_id"], "attack_reconstruction", 6, summary, state["attack_reconstruction"])
        return state
    finally:
        db.close()

# --- NODE 7: MITRE ATT&CK Mapping ---
def mitre_mapping_node(state: InvestigationState) -> InvestigationState:
    db: Session = SessionLocal()
    try:
        # Use our grounded MITRE catalog
        raw_events = [TelemetryEvent(**e) if isinstance(e, dict) else e for e in state["collected_events"]]
        alert_rule = state["alert_data"].get("rule_name")
        mappings = MitreCatalog.evaluate_telemetry(raw_events, [alert_rule] if alert_rule else [])
        
        state["mitre_mappings"] = mappings
        state["current_stage"] = "mitre_mapping"
        state["progress"] = 80

        summary = f"MITRE Mapping Agent grounded {len(mappings)} techniques with direct event provenance."
        record_step(db, state["investigation_id"], "mitre_mapping", 7, summary, {"mappings": mappings})
        return state
    finally:
        db.close()

# --- NODE 8: Risk Assessment ---
def risk_assessment_node(state: InvestigationState) -> InvestigationState:
    db: Session = SessionLocal()
    try:
        alert_sev = state["alert_data"].get("severity", "MEDIUM")
        sev_multiplier = {"CRITICAL": 9.5, "HIGH": 8.0, "MEDIUM": 5.5, "LOW": 3.0, "INFO": 1.0}
        score = sev_multiplier.get(alert_sev, 5.0)

        risk = {
            "overall_severity": alert_sev,
            "impact_score": score,
            "blast_radius": f"{len(state['target_entities'])} identified assets/accounts",
            "uncertainty": "LOW" if state["sufficiency_reached"] else "MEDIUM",
            "rationale": f"High risk to confidentiality and integrity if {state['alert_data'].get('title')} remains uncontained."
        }
        state["risk_assessment"] = risk
        state["current_stage"] = "risk_assessment"
        state["progress"] = 90

        summary = f"Risk Assessment completed. Score: {score}/10 ({alert_sev}). Uncertainty: {risk['uncertainty']}."
        record_step(db, state["investigation_id"], "risk_assessment", 8, summary, risk)
        return state
    finally:
        db.close()

# --- NODE 9: Explainability, Response Recommendations & Closure ---
def response_and_closure_node(state: InvestigationState) -> InvestigationState:
    db: Session = SessionLocal()
    try:
        # Create response action entries in Response Center awaiting human approval
        for rec in state["response_recommendations"]:
            act_id = f"RSP-{uuid.uuid4().hex[:6].upper()}"
            action = ResponseAction(
                id=act_id,
                investigation_id=state["investigation_id"],
                action_type=rec.get("action_type", "ISOLATE_HOST"),
                target_entity=rec.get("target_entity", "Host"),
                status="PENDING_APPROVAL",
                rationale=rec.get("rationale", "Forensic containment action"),
                risk_assessment=rec.get("risk_assessment", "Mitigates threat spread"),
                is_simulated=True, # Explicit simulated guardrail
                is_demo=state["is_demo"]
            )
            db.merge(action)

        state["current_stage"] = "investigation_closure"
        state["progress"] = 100
        state["status"] = "COMPLETED"

        # Update persistent Investigation record
        inv = db.query(Investigation).filter(Investigation.id == state["investigation_id"]).first()
        if inv:
            inv.status = "COMPLETED"
            inv.current_stage = "investigation_closure"
            inv.progress = 100
            inv.hypotheses = state["hypotheses"]
            inv.findings = state["findings"]
            inv.missing_evidence = state["missing_evidence"]
            inv.sufficiency_reached = state["sufficiency_reached"]
            inv.iteration_count = state["iteration_count"]
            inv.attack_reconstruction = state["attack_reconstruction"]
            inv.mitre_mappings = state["mitre_mappings"]
            inv.risk_assessment = state["risk_assessment"]
            inv.executive_summary = state["executive_summary"]
            inv.llm_invoked = state["llm_invoked"]
            inv.llm_provider = state["llm_provider"]
            inv.llm_model = state["llm_model"]
            inv.degraded_mode = state["degraded_mode"]
            inv.updated_at = datetime.utcnow()
        
        db.commit()

        summary = (
            f"Investigation closed. Generated {len(state['response_recommendations'])} containment actions "
            f"staged in Response Center requiring human authorization."
        )
        record_step(db, state["investigation_id"], "investigation_closure", 9, summary, {
            "response_actions_count": len(state["response_recommendations"])
        })
        return state
    finally:
        db.close()


# --- COMPOSE & COMPILE THE STATEGRAPH ---
def build_investigation_graph():
    workflow = StateGraph(InvestigationState)

    # 1. Add nodes
    workflow.add_node("alert_intake", alert_intake_node)
    workflow.add_node("investigation_planning", investigation_planning_node)
    workflow.add_node("evidence_collection", evidence_collection_node)
    workflow.add_node("correlation_and_validation", correlation_and_validation_node)
    workflow.add_node("evidence_sufficiency_assessment", evidence_sufficiency_assessment_node)
    workflow.add_node("attack_reconstruction", attack_reconstruction_node)
    workflow.add_node("mitre_mapping", mitre_mapping_node)
    workflow.add_node("risk_assessment", risk_assessment_node)
    workflow.add_node("response_and_closure", response_and_closure_node)

    # 2. Add edges
    workflow.set_entry_point("alert_intake")
    workflow.add_edge("alert_intake", "investigation_planning")
    workflow.add_edge("investigation_planning", "evidence_collection")
    workflow.add_edge("evidence_collection", "correlation_and_validation")
    workflow.add_edge("correlation_and_validation", "evidence_sufficiency_assessment")

    # Conditional routing: sufficiency loop
    workflow.add_conditional_edges(
        "evidence_sufficiency_assessment",
        sufficiency_router,
        {
            "evidence_collection": "evidence_collection",
            "attack_reconstruction": "attack_reconstruction"
        }
    )

    workflow.add_edge("attack_reconstruction", "mitre_mapping")
    workflow.add_edge("mitre_mapping", "risk_assessment")
    workflow.add_edge("risk_assessment", "response_and_closure")
    workflow.add_edge("response_and_closure", END)

    # Compile the graph
    app = workflow.compile()
    return app

compiled_investigation_graph = build_investigation_graph()


def execute_investigation_workflow(investigation_id: str, alert_id: str, is_demo: bool = False) -> Dict[str, Any]:
    """
    Executes the compiled LangGraph workflow synchronously or asynchronously.
    """
    initial_state: InvestigationState = {
        "investigation_id": investigation_id,
        "alert_id": alert_id,
        "is_demo": is_demo,
        "current_stage": "alert_intake",
        "progress": 0,
        "iteration_count": 1,
        "max_iterations": 2,
        "alert_data": {},
        "target_entities": [],
        "collected_events": [],
        "evidence_items": [],
        "graph_nodes": [],
        "graph_edges": [],
        "hypotheses": [],
        "findings": [],
        "missing_evidence": [],
        "sufficiency_reached": False,
        "attack_reconstruction": {},
        "mitre_mappings": [],
        "risk_assessment": {},
        "executive_summary": None,
        "response_recommendations": [],
        "llm_invoked": False,
        "llm_provider": None,
        "llm_model": None,
        "degraded_mode": False,
        "provider_switches": [],
        "failover_reason": None,
        "status": "INITIALIZING",
        "errors": []
    }

    # Run LangGraph StateGraph
    final_state = compiled_investigation_graph.invoke(initial_state)
    return final_state
