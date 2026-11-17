from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertResponse
from app.services.detection.rule_engine import RuleDetectionEngine
from app.services.detection.isolation_forest_engine import IsolationForestEngine

router = APIRouter()

@router.get("", response_model=List[AlertResponse])
def get_alerts(
    is_demo: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    detection_method: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Alert)
    if is_demo is not None:
        query = query.filter(Alert.is_demo == is_demo)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if detection_method:
        query = query.filter(Alert.detection_method == detection_method.upper())
    if status:
        query = query.filter(Alert.status == status.upper())

    alerts = query.order_by(Alert.created_at.desc()).offset(offset).limit(limit).all()
    return alerts

@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert_by_id(alert_id: str, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert

@router.post("/detect")
def trigger_detection(
    is_demo: bool = Query(False),
    contamination: float = Query(0.15, ge=0.01, le=0.4),
    db: Session = Depends(get_db)
):
    # Run both Rule-Based and Isolation Forest detection
    rule_alerts = RuleDetectionEngine.run_detection(db, is_demo=is_demo)
    ml_alerts = IsolationForestEngine.run_detection(db, is_demo=is_demo, contamination=contamination)

    return {
        "message": f"Detection executed successfully.",
        "rule_alerts_generated": len(rule_alerts),
        "ml_anomalies_detected": len(ml_alerts),
        "is_demo": is_demo
    }
