from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.response import ResponseAction, ApprovalHistory
from app.schemas.response import (
    ResponseActionResponse,
    ApprovalHistoryResponse,
    ResponseApprovalRequest
)
from app.services.response.response_service import ResponseService

router = APIRouter()

@router.get("", response_model=List[ResponseActionResponse])
def get_response_actions(
    investigation_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_demo: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ResponseAction)
    if investigation_id:
        query = query.filter(ResponseAction.investigation_id == investigation_id)
    if status:
        query = query.filter(ResponseAction.status == status.upper())
    if is_demo is not None:
        query = query.filter(ResponseAction.is_demo == is_demo)

    return query.order_by(ResponseAction.created_at.desc()).all()

@router.post("/{action_id}/approve", response_model=ResponseActionResponse)
def approve_action(
    action_id: str,
    payload: ResponseApprovalRequest,
    db: Session = Depends(get_db)
):
    try:
        return ResponseService.approve_action(
            action_id=action_id,
            decided_by=payload.decided_by,
            comments=payload.comments,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{action_id}/reject", response_model=ResponseActionResponse)
def reject_action(
    action_id: str,
    payload: ResponseApprovalRequest,
    db: Session = Depends(get_db)
):
    try:
        return ResponseService.reject_action(
            action_id=action_id,
            decided_by=payload.decided_by,
            comments=payload.comments,
            db=db
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/history", response_model=List[ApprovalHistoryResponse])
def get_approval_history(
    investigation_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(ApprovalHistory)
    if investigation_id:
        query = query.filter(ApprovalHistory.investigation_id == investigation_id)
    return query.order_by(ApprovalHistory.timestamp.desc()).all()
