from typing import Optional, List
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.telemetry import TelemetryEvent
from app.models.alert import Alert
from app.schemas.telemetry import IngestionResult, TelemetryEventResponse
from app.services.ingestion.telemetry_service import TelemetryService
from app.services.detection.rule_engine import RuleDetectionEngine
from app.services.detection.isolation_forest_engine import IsolationForestEngine

router = APIRouter()

@router.post("/upload", response_model=IngestionResult)
async def upload_telemetry(
    file: UploadFile = File(...),
    is_demo: bool = Form(False),
    run_detection_after: bool = Form(True),
    db: Session = Depends(get_db)
):
    # Check file size limit
    content_bytes = await file.read()
    size_mb = len(content_bytes) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(status_code=400, detail=f"File exceeds maximum upload size of {settings.MAX_UPLOAD_SIZE_MB}MB")

    try:
        content_str = content_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            content_str = content_bytes.decode("latin-1")
        except Exception:
            raise HTTPException(status_code=400, detail="Unable to decode file text encoding.")

    result = TelemetryService.parse_and_ingest(
        content=content_str,
        filename=file.filename,
        db=db,
        is_demo=is_demo,
        dataset_source=f"upload:{file.filename}"
    )

    if run_detection_after and result.valid_count > 0:
        # Automatically run rule detection and isolation forest
        RuleDetectionEngine.run_detection(db, is_demo=is_demo)
        if result.valid_count >= 4:
            IsolationForestEngine.run_detection(db, is_demo=is_demo)

    return result

@router.get("", response_model=List[TelemetryEventResponse])
def get_telemetry(
    is_demo: Optional[bool] = Query(None),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    host: Optional[str] = Query(None),
    user: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(TelemetryEvent)
    if is_demo is not None:
        query = query.filter(TelemetryEvent.is_demo == is_demo)
    if event_type:
        query = query.filter(TelemetryEvent.event_type == event_type.upper())
    if severity:
        query = query.filter(TelemetryEvent.severity == severity.upper())
    if host:
        query = query.filter(TelemetryEvent.host.ilike(f"%{host}%"))
    if user:
        query = query.filter(TelemetryEvent.user.ilike(f"%{user}%"))

    events = query.order_by(TelemetryEvent.timestamp.desc()).offset(offset).limit(limit).all()
    return events

@router.delete("")
def clear_telemetry(is_demo: Optional[bool] = Query(None), db: Session = Depends(get_db)):
    query = db.query(TelemetryEvent)
    alt_query = db.query(Alert)
    if is_demo is not None:
        query = query.filter(TelemetryEvent.is_demo == is_demo)
        alt_query = alt_query.filter(Alert.is_demo == is_demo)
    
    deleted = query.delete(synchronize_session=False)
    alt_query.delete(synchronize_session=False)
    db.commit()
    return {"message": f"Successfully cleared {deleted} telemetry records and associated alerts."}
