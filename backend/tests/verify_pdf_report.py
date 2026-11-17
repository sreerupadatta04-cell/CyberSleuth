import sys
import io
import urllib.request
from pathlib import Path
from pypdf import PdfReader

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import SessionLocal
from app.models.investigation import Investigation
from app.services.reporting.pdf_generator import PDFReportGenerator

def test_pdf_report():
    db = SessionLocal()
    
    # Ensure at least one completed investigation exists
    inv = db.query(Investigation).filter(Investigation.status == "COMPLETED").first()
    if not inv:
        from app.services.ingestion.telemetry_service import TelemetryService
        from app.services.detection.rule_engine import RuleDetectionEngine
        from app.services.agentic.graph import execute_investigation_workflow
        demo_dir = Path(__file__).resolve().parent.parent.parent / "datasets" / "demo"
        with open(demo_dir / "credential_compromise.json", "r", encoding="utf-8") as f:
            TelemetryService.parse_and_ingest(f.read(), "credential_compromise.json", db, is_demo=True)
        alerts = RuleDetectionEngine.run_detection(db, is_demo=True)
        inv_id = "INV-AUDIT-PDF-01"
        inv = Investigation(id=inv_id, alert_id=alerts[0].id, status="INITIALIZING", is_demo=True)
        db.merge(inv)
        db.commit()
        execute_investigation_workflow(inv_id, alerts[0].id, is_demo=True)
        inv = db.query(Investigation).filter(Investigation.id == inv_id).first()

    assert inv is not None, "Need a completed investigation to audit PDF"
    print(f"Auditing PDF Report for Investigation: {inv.id}")

    # 1. Generate PDF bytes
    pdf_bytes = PDFReportGenerator.generate_investigation_report(inv.id, db)
    assert pdf_bytes.startswith(b"%PDF"), "Missing %PDF magic bytes"
    assert b"%%EOF" in pdf_bytes[-1024:], "Missing %%EOF marker"
    print(f"1. PDF Binary Structure Confirmed: {len(pdf_bytes)} bytes")

    # 2. Extract and inspect text using pypdf
    reader = PdfReader(io.BytesIO(pdf_bytes))
    print(f"2. PDF Page count: {len(reader.pages)}")
    assert len(reader.pages) >= 1

    extracted_text = ""
    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        extracted_text += f"\n--- Page {idx+1} ---\n" + text

    print("--- Extracted PDF Content Preview ---")
    print(extracted_text[:600])
    print("-------------------------------------")

    # Verify key tokens and forensic sections
    assert "CYBERSLEUTH FORENSIC INVESTIGATION" in extracted_text
    assert inv.id in extracted_text, f"Investigation ID {inv.id} not found in text"
    assert "1. Executive Summary" in extracted_text
    assert "2. Triggering Alert Context" in extracted_text
    assert "3. Evidence-Grounded Findings" in extracted_text
    assert "4. Attack Reconstruction & Timeline" in extracted_text
    assert "5. Grounded MITRE ATT&CK Alignment" in extracted_text
    assert "6. Incident Response & Human Approval History" in extracted_text
    assert "7. Investigation Limitations & Boundary Statement" in extracted_text
    assert "OBSERVED" in extracted_text or "INFERRED" in extracted_text
    print("3. All 7 mandatory forensic sections and provenance labels verified!")

    # 4. Test HTTP Download endpoint
    url = f"http://127.0.0.1:8000/api/reports/{inv.id}/download"
    req = urllib.request.urlopen(url)
    assert req.status == 200
    assert req.headers["content-type"] == "application/pdf"
    assert f"CyberSleuth_Report_{inv.id}.pdf" in req.headers["content-disposition"]
    print("4. Live HTTP PDF download endpoint verified (Status: 200, Content-Type: application/pdf).")

    print("PDF Verification: 100% PASSED!")
    db.close()

if __name__ == "__main__":
    test_pdf_report()
