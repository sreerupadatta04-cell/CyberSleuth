from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.investigation import Investigation
from app.models.alert import Alert
from app.services.reporting.pdf_generator import PDFReportGenerator

router = APIRouter()

@router.get("/{investigation_id}")
def get_report_metadata(investigation_id: str, db: Session = Depends(get_db)):
    inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    alert = db.query(Alert).filter(Alert.id == inv.alert_id).first()

    return {
        "investigation_id": inv.id,
        "alert_id": inv.alert_id,
        "title": alert.title if alert else "Investigation Report",
        "severity": alert.severity if alert else "MEDIUM",
        "status": inv.status,
        "executive_summary": inv.executive_summary,
        "findings_count": len(inv.findings or []),
        "mitre_mappings_count": len(inv.mitre_mappings or []),
        "sufficiency_reached": inv.sufficiency_reached,
        "llm_provider": inv.llm_provider,
        "degraded_mode": inv.degraded_mode,
        "created_at": inv.created_at.isoformat(),
        "pdf_download_url": f"/api/reports/{investigation_id}/download"
    }

@router.get("/{investigation_id}/download")
def download_pdf_report(investigation_id: str, db: Session = Depends(get_db)):
    try:
        pdf_bytes = PDFReportGenerator.generate_investigation_report(investigation_id, db)
        filename = f"CyberSleuth_Report_{investigation_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
