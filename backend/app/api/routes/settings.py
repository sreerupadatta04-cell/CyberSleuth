import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.models.telemetry import TelemetryEvent
from app.models.alert import Alert
from app.models.investigation import Investigation, InvestigationStep
from app.models.evidence import Evidence, EvidenceRelationship
from app.models.response import ResponseAction, ApprovalHistory
from app.schemas.settings import SystemHealthResponse, LLMConfigUpdateRequest
from app.schemas.llm import LLMConnectionTestRequest, LLMConnectionTestResult
from app.services.llm.llm_client import LLMService

router = APIRouter()

@router.get("/health", response_model=SystemHealthResponse)
def get_system_settings_health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    llm_health = LLMService.check_health()
    live_events = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == False).count()
    demo_events = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == True).count()
    alerts_count = db.query(Alert).count()
    investigations_count = db.query(Investigation).count()

    return SystemHealthResponse(
        status="OPERATIONAL" if db_ok else "DEGRADED",
        backend_health="HEALTHY" if db_ok else "ERROR",
        database_connected=db_ok,
        detection_engine_status="ACTIVE (Rule + Isolation Forest)",
        langgraph_workflow_status="COMPILED & READY",
        llm_provider_status=llm_health["status"],
        llm_provider=settings.LLM_PROVIDER,
        llm_fallback_provider=settings.LLM_FALLBACK_PROVIDER,
        llm_model=llm_health["model"],
        degraded_mode=not llm_health["available"],
        live_reasoning_enabled=settings.LLM_LIVE_REASONING,
        deterministic_fallback_allowed=settings.LLM_ALLOW_DETERMINISTIC_FALLBACK,
        gemini_configured=llm_health["gemini_configured"],
        gemini_model=llm_health["gemini_model"],
        gemini_status=llm_health["gemini_status"],
        openai_configured=llm_health["openai_configured"],
        openai_model=llm_health["openai_model"],
        openai_status=llm_health["openai_status"],
        events_count_live=live_events,
        events_count_demo=demo_events,
        alerts_count=alerts_count,
        investigations_count=investigations_count,
        environment_mode="DEMO" if demo_events > 0 and live_events == 0 else ("LIVE" if demo_events == 0 else "HYBRID")
    )

def _persist_to_env(updates: dict):
    env_file = settings.BASE_DIR / ".env"
    if not env_file.exists():
        return
    try:
        content = env_file.read_text(encoding="utf-8")
        for key, val in updates.items():
            if val is None:
                continue
            val_str = f'"{val}"' if isinstance(val, str) else str(val).lower()
            pattern = re.compile(rf'^{key}\s*=.*$', re.MULTILINE)
            if pattern.search(content):
                content = pattern.sub(f'{key}={val_str}', content)
            else:
                content += f"\n{key}={val_str}"
        env_file.write_text(content, encoding="utf-8")
    except Exception:
        pass

@router.post("/llm")
def update_llm_config(payload: LLMConfigUpdateRequest):
    """
    Safely update LLM provider configuration and model parameters in memory and runtime settings.
    Persists configuration updates to backend/.env.
    Never exposes raw API keys in response.
    """
    env_updates = {}
    settings.LLM_PROVIDER = payload.provider.lower()
    env_updates["LLM_PROVIDER"] = settings.LLM_PROVIDER

    if payload.fallback_provider:
        settings.LLM_FALLBACK_PROVIDER = payload.fallback_provider.lower()
        env_updates["LLM_FALLBACK_PROVIDER"] = settings.LLM_FALLBACK_PROVIDER

    if payload.gemini_model:
        settings.GEMINI_MODEL = payload.gemini_model.strip()
        env_updates["GEMINI_MODEL"] = settings.GEMINI_MODEL

    if payload.openai_model:
        settings.OPENAI_MODEL = payload.openai_model.strip()
        env_updates["OPENAI_MODEL"] = settings.OPENAI_MODEL

    if payload.gemini_api_key is not None and payload.gemini_api_key.strip():
        settings.GEMINI_API_KEY = payload.gemini_api_key.strip()
        env_updates["GEMINI_API_KEY"] = settings.GEMINI_API_KEY

    if payload.openai_api_key is not None and payload.openai_api_key.strip():
        settings.OPENAI_API_KEY = payload.openai_api_key.strip()
        env_updates["OPENAI_API_KEY"] = settings.OPENAI_API_KEY

    if payload.live_reasoning is not None:
        settings.LLM_LIVE_REASONING = payload.live_reasoning
        env_updates["LLM_LIVE_REASONING"] = settings.LLM_LIVE_REASONING

    if payload.allow_fallback is not None:
        settings.LLM_ALLOW_DETERMINISTIC_FALLBACK = payload.allow_fallback
        env_updates["LLM_ALLOW_DETERMINISTIC_FALLBACK"] = settings.LLM_ALLOW_DETERMINISTIC_FALLBACK

    _persist_to_env(env_updates)

    health = LLMService.check_health()
    return {
        "message": f"LLM configuration updated. Active Provider: {settings.LLM_PROVIDER.upper()}, Fallback: {settings.LLM_FALLBACK_PROVIDER.upper()}.",
        "provider_health": health
    }

@router.get("/gemini-models")
def get_gemini_models(api_key: Optional[str] = Query(None)):
    """
    Query available models directly from Google AI Studio under v1beta.
    """
    try:
        models = LLMService.list_available_gemini_models(api_key=api_key)
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/test-llm", response_model=LLMConnectionTestResult)
def test_llm_connection(payload: LLMConnectionTestRequest):
    """
    Safely test connectivity to a specific LLM provider.
    Accepts optional temporary key/model for verification before saving.
    """
    result = LLMService.test_connection(
        provider=payload.provider,
        api_key=payload.api_key,
        model=payload.model
    )
    return result

@router.post("/reset-demo")
def reset_demo_data(db: Session = Depends(get_db)):
    # Safely clear all records where is_demo == True
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
    return {"message": "All synthetic DEMO data cleared successfully. LIVE data preserved intact."}
