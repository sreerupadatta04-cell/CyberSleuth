from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceItemResponse, EvidenceGraphResponse
from app.services.evidence.evidence_graph_service import EvidenceGraphService

router = APIRouter()

@router.get("/{investigation_id}", response_model=List[EvidenceItemResponse])
def get_evidence_items(investigation_id: str, db: Session = Depends(get_db)):
    items = db.query(Evidence).filter(Evidence.investigation_id == investigation_id).all()
    return items

@router.get("/{investigation_id}/graph", response_model=EvidenceGraphResponse)
def get_evidence_graph(investigation_id: str, db: Session = Depends(get_db)):
    return EvidenceGraphService.get_investigation_graph(investigation_id, db)
