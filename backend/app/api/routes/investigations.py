import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db, SessionLocal
from app.models.investigation import Investigation, InvestigationStep
from app.models.alert import Alert
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationResponse,
    InvestigationProgressResponse
)
from app.services.agentic.graph import execute_investigation_workflow

router = APIRouter()

def run_workflow_task(investigation_id: str, alert_id: str, is_demo: bool):
    try:
        execute_investigation_workflow(investigation_id, alert_id, is_demo)
    except Exception as e:
        print(f"[Investigation Workflow Error] {str(e)}")
        db = SessionLocal()
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if inv:
            inv.status = "FAILED"
            inv.current_stage = "error"
            db.commit()
        db.close()

@router.post("", response_model=InvestigationResponse)
def create_investigation(
    payload: InvestigationCreate,
    background_tasks: BackgroundTasks,
    run_async: bool = Query(False),
    force: bool = Query(False),
    db: Session = Depends(get_db)
):
    alert = db.query(Alert).filter(Alert.id == payload.alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail=f"Alert {payload.alert_id} not found.")

    # Check if investigation already exists for this alert
    existing = db.query(Investigation).filter(Investigation.alert_id == alert.id).order_by(Investigation.created_at.desc()).first()
    if existing and existing.status == "COMPLETED" and not existing.degraded_mode and not force:
        return existing

    inv_id = f"INV-{uuid.uuid4().hex[:6].upper()}"
    inv = Investigation(
        id=inv_id,
        alert_id=alert.id,
        status="INITIALIZING",
        current_stage="alert_intake",
        progress=0,
        is_demo=alert.is_demo
    )
    db.add(inv)
    alert.investigation_id = inv_id
    db.commit()
    db.refresh(inv)

    if run_async:
        background_tasks.add_task(run_workflow_task, inv.id, alert.id, alert.is_demo)
    else:
        # Run synchronous invocation of the real LangGraph StateGraph
        execute_investigation_workflow(inv.id, alert.id, alert.is_demo)
        db.refresh(inv)

    return inv

@router.get("", response_model=List[InvestigationResponse])
def get_investigations(
    is_demo: Optional[bool] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    query = db.query(Investigation)
    if is_demo is not None:
        query = query.filter(Investigation.is_demo == is_demo)
    if status:
        query = query.filter(Investigation.status == status.upper())

    return query.order_by(Investigation.created_at.desc()).offset(offset).limit(limit).all()

@router.get("/{investigation_id}", response_model=InvestigationResponse)
def get_investigation_by_id(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    return inv

@router.get("/{investigation_id}/progress", response_model=InvestigationProgressResponse)
def get_investigation_progress(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found.")
    
    latest_step = db.query(InvestigationStep).filter(
        InvestigationStep.investigation_id == investigation_id
    ).order_by(InvestigationStep.step_order.desc()).first()

    return InvestigationProgressResponse(
        id=inv.id,
        status=inv.status,
        current_stage=inv.current_stage,
        progress=inv.progress,
        updated_at=inv.updated_at,
        latest_step=latest_step
    )
