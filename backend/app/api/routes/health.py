from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.models.telemetry import TelemetryEvent
from app.models.alert import Alert
from app.models.investigation import Investigation
from app.services.llm.llm_client import LLMService

router = APIRouter()

@router.get("/health")
def get_health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    llm_health = LLMService.check_health()

    return {
        "status": "healthy" if db_ok else "unhealthy",
        "backend": "online",
        "database": "connected" if db_ok else "disconnected",
        "llm_provider": llm_health["provider"],
        "llm_status": llm_health["status"],
        "degraded_mode": not llm_health["available"],
        "version": settings.VERSION
    }

@router.get("/overview")
def get_overview(db: Session = Depends(get_db)):
    total_events = db.query(TelemetryEvent).count()
    live_events = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == False).count()
    demo_events = db.query(TelemetryEvent).filter(TelemetryEvent.is_demo == True).count()
    
    total_alerts = db.query(Alert).count()
    active_alerts = db.query(Alert).filter(Alert.status.in_(["NEW", "INVESTIGATING"])).count()
    critical_alerts = db.query(Alert).filter(Alert.severity == "CRITICAL").count()
    
    investigations_running = db.query(Investigation).filter(Investigation.status == "IN_PROGRESS").count()
    investigations_completed = db.query(Investigation).filter(Investigation.status == "COMPLETED").count()
    
    rule_alerts = db.query(Alert).filter(Alert.detection_method == "RULE_BASED").count()
    ml_alerts = db.query(Alert).filter(Alert.detection_method == "ISOLATION_FOREST").count()

    # Recent activity
    recent_events = db.query(TelemetryEvent).order_by(TelemetryEvent.timestamp.desc()).limit(10).all()
    recent_investigations = db.query(Investigation).order_by(Investigation.created_at.desc()).limit(5).all()

    # Severity distribution
    severity_dist = {
        "CRITICAL": db.query(Alert).filter(Alert.severity == "CRITICAL").count(),
        "HIGH": db.query(Alert).filter(Alert.severity == "HIGH").count(),
        "MEDIUM": db.query(Alert).filter(Alert.severity == "MEDIUM").count(),
        "LOW": db.query(Alert).filter(Alert.severity == "LOW").count(),
    }

    return {
        "metrics": {
            "total_events": total_events,
            "live_events": live_events,
            "demo_events": demo_events,
            "total_alerts": total_alerts,
            "active_alerts": active_alerts,
            "critical_threats": critical_alerts,
            "investigations_running": investigations_running,
            "investigations_completed": investigations_completed,
            "detected_anomalies": ml_alerts,
            "rule_detections": rule_alerts
        },
        "severity_distribution": [
            {"name": k, "value": v} for k, v in severity_dist.items()
        ],
        "detection_types": [
            {"name": "Rule-Based Engine", "value": rule_alerts},
            {"name": "Isolation Forest (ML)", "value": ml_alerts}
        ],
        "recent_investigations": [
            {
                "id": inv.id,
                "alert_id": inv.alert_id,
                "status": inv.status,
                "stage": inv.current_stage,
                "progress": inv.progress,
                "created_at": inv.created_at.isoformat()
            }
            for inv in recent_investigations
        ],
        "recent_events": [
            {
                "id": ev.id,
                "type": ev.event_type,
                "severity": ev.severity,
                "user": ev.user,
                "host": ev.host,
                "timestamp": ev.timestamp.isoformat(),
                "is_demo": ev.is_demo
            }
            for ev in recent_events
        ]
    }
