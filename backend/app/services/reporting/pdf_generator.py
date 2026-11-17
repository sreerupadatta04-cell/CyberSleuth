import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from sqlalchemy.orm import Session
from app.models.investigation import Investigation
from app.models.alert import Alert
from app.models.response import ResponseAction, ApprovalHistory

class PDFReportGenerator:
    @staticmethod
    def generate_investigation_report(investigation_id: str, db: Session) -> bytes:
        inv = db.query(Investigation).filter(Investigation.id == investigation_id).first()
        if not inv:
            raise ValueError(f"Investigation {investigation_id} not found.")

        alert = db.query(Alert).filter(Alert.id == inv.alert_id).first()
        actions = db.query(ResponseAction).filter(ResponseAction.investigation_id == investigation_id).all()
        approvals = db.query(ApprovalHistory).filter(ApprovalHistory.investigation_id == investigation_id).all()

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # CyberSleuth Palette
        brand_teal = colors.HexColor("#033C42")
        brand_cyan = colors.HexColor("#00D5C5")
        brand_charcoal = colors.HexColor("#101C1D")
        bg_alt = colors.HexColor("#F0F5F4")

        # Custom typography styles
        title_style = ParagraphStyle(
            "CS_Title",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=brand_teal,
            fontName="Helvetica-Bold"
        )
        subtitle_style = ParagraphStyle(
            "CS_Subtitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#556B69")
        )
        h2_style = ParagraphStyle(
            "CS_H2",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=brand_teal,
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "CS_Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=brand_charcoal
        )
        badge_observed = ParagraphStyle(
            "BadgeObserved",
            parent=styles["Normal"],
            fontSize=8,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#0B7A75")
        )
        badge_inferred = ParagraphStyle(
            "BadgeInferred",
            parent=styles["Normal"],
            fontSize=8,
            fontName="Helvetica-Bold",
            textColor=colors.HexColor("#B26E00")
        )

        story = []

        # 1. Header & Branding
        story.append(Paragraph("CYBERSLEUTH FORENSIC INVESTIGATION REPORT", title_style))
        story.append(Paragraph(
            f"Autonomous Multi-Agent Cybersecurity Incident Investigation Framework | Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            subtitle_style
        ))
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=2, color=brand_teal, spaceAfter=10))

        # 2. Metadata Table
        meta_data = [
            [
                Paragraph("<b>Investigation ID:</b>", body_style),
                Paragraph(inv.id, body_style),
                Paragraph("<b>Status:</b>", body_style),
                Paragraph(inv.status, body_style)
            ],
            [
                Paragraph("<b>Alert ID:</b>", body_style),
                Paragraph(inv.alert_id, body_style),
                Paragraph("<b>Severity:</b>", body_style),
                Paragraph(alert.severity if alert else "N/A", body_style)
            ],
            [
                Paragraph("<b>LLM Provider:</b>", body_style),
                Paragraph(f"{inv.llm_provider or 'Deterministic Fallback'}", body_style),
                Paragraph("<b>Degraded Mode:</b>", body_style),
                Paragraph("TRUE (Fallback)" if inv.degraded_mode else "FALSE (Live LLM)", body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[100, 170, 100, 170])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), bg_alt),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0DCDC")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 12))

        # 3. Executive Summary
        story.append(Paragraph("1. Executive Summary", h2_style))
        exec_text = inv.executive_summary or (alert.description if alert else "Investigation initiated.")
        story.append(Paragraph(exec_text, body_style))
        story.append(Spacer(1, 10))

        # 4. Alert & Trigger Details
        story.append(Paragraph("2. Triggering Alert Context", h2_style))
        alert_desc = alert.explanation or (alert.description if alert else "No alert data")
        story.append(Paragraph(f"<b>Title:</b> {alert.title if alert else 'Unknown'}", body_style))
        story.append(Paragraph(f"<b>Detection Method:</b> {alert.detection_method if alert else 'N/A'}", body_style))
        story.append(Paragraph(f"<b>Explanation:</b> {alert_desc}", body_style))
        story.append(Spacer(1, 10))

        # 5. Structured Forensic Findings (OBSERVED vs INFERRED)
        story.append(Paragraph("3. Evidence-Grounded Findings", h2_style))
        findings_data = [
            [
                Paragraph("<b>ID</b>", body_style),
                Paragraph("<b>Status</b>", body_style),
                Paragraph("<b>Confidence</b>", body_style),
                Paragraph("<b>Finding Statement</b>", body_style),
                Paragraph("<b>Supporting Events</b>", body_style)
            ]
        ]
        for f in (inv.findings or []):
            st = f.get("status", "OBSERVED")
            badge = badge_observed if st == "OBSERVED" else badge_inferred
            conf = f"{int(f.get('confidence', 1.0) * 100)}%"
            stmt = f.get("statement", "")
            supp = ", ".join(f.get("supporting_events", [])) or "N/A"
            findings_data.append([
                Paragraph(f.get("id", "FND"), body_style),
                Paragraph(st, badge),
                Paragraph(conf, body_style),
                Paragraph(stmt, body_style),
                Paragraph(supp, body_style)
            ])

        if len(findings_data) > 1:
            findings_table = Table(findings_data, colWidths=[55, 65, 55, 255, 110])
            findings_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), brand_teal),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0DCDC")),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(findings_table)
        else:
            story.append(Paragraph("No structured findings recorded.", body_style))
        story.append(Spacer(1, 12))

        # 6. Attack Reconstruction Narrative
        story.append(Paragraph("4. Attack Reconstruction & Timeline", h2_style))
        recon_narrative = (inv.attack_reconstruction or {}).get("narrative", "Attack reconstruction sequence generated by multi-agent analysis.")
        story.append(Paragraph(recon_narrative.replace("\n", "<br/>"), body_style))
        story.append(Spacer(1, 10))

        # 7. MITRE ATT&CK Mapping
        story.append(Paragraph("5. Grounded MITRE ATT&amp;CK Alignment", h2_style))
        mitre_data = [
            [
                Paragraph("<b>Technique ID</b>", body_style),
                Paragraph("<b>Tactic</b>", body_style),
                Paragraph("<b>Technique Name</b>", body_style),
                Paragraph("<b>Evidence Citations</b>", body_style)
            ]
        ]
        for m in (inv.mitre_mappings or []):
            mitre_data.append([
                Paragraph(m.get("technique_id", ""), body_style),
                Paragraph(m.get("tactic", ""), body_style),
                Paragraph(m.get("name", ""), body_style),
                Paragraph(", ".join(m.get("supporting_events", [])), body_style)
            ])

        if len(mitre_data) > 1:
            mitre_table = Table(mitre_data, colWidths=[80, 120, 160, 180])
            mitre_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), brand_teal),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0DCDC")),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(mitre_table)
        else:
            story.append(Paragraph("No MITRE ATT&CK techniques mapped.", body_style))
        story.append(Spacer(1, 12))

        # 8. Human-in-the-Loop Response Actions
        story.append(Paragraph("6. Incident Response & Human Approval History", h2_style))
        action_data = [
            [
                Paragraph("<b>Action ID</b>", body_style),
                Paragraph("<b>Action Type</b>", body_style),
                Paragraph("<b>Target Entity</b>", body_style),
                Paragraph("<b>Status</b>", body_style),
                Paragraph("<b>Decided By</b>", body_style)
            ]
        ]
        for a in actions:
            action_data.append([
                Paragraph(a.id, body_style),
                Paragraph(a.action_type, body_style),
                Paragraph(a.target_entity, body_style),
                Paragraph(a.status, body_style),
                Paragraph(a.decided_by or "Pending", body_style)
            ])

        if len(action_data) > 1:
            act_table = Table(action_data, colWidths=[70, 120, 120, 100, 130])
            act_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), brand_teal),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D0DCDC")),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ]))
            story.append(act_table)
        else:
            story.append(Paragraph("No response actions staged.", body_style))
        story.append(Spacer(1, 12))

        # 9. Limitations & Research Disclaimer
        story.append(Paragraph("7. Investigation Limitations & Boundary Statement", h2_style))
        disclaimer = (
            "CyberSleuth operates as an evidence-driven, LLM-assisted multi-agent framework. "
            "All findings designated 'OBSERVED' are strictly constrained by ingested telemetry records. "
            "Findings designated 'INFERRED' represent statistical or heuristic correlations. "
            "In accordance with safety guardrails, autonomous containment execution is prohibited: "
            "all response measures require explicit human verification and authorization before dispatch."
        )
        story.append(Paragraph(disclaimer, subtitle_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
