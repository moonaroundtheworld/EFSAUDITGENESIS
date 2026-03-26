import os
from reportlab.lib.pagesizes import letter # type: ignore
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak # type: ignore
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle # type: ignore
from reportlab.lib import colors # type: ignore
from datetime import datetime

def generate_audit_opinion(total_risk_exposure: float, heatmap: dict, materiality_threshold: float = 1000000.0) -> str:
    top_rule = max(heatmap.items(), key=lambda x: x[1])[0] if heatmap else None
    basis = f" Basis for Opinion: Extensively mapped failures linked explicitly to '{top_rule}'." if top_rule else ""
        
    if total_risk_exposure > materiality_threshold:
        return f"MODIFIED OPINION (Adverse / Qualified): The financial records present a Material Misstatement.{basis} Verified risk exposure (PKR {total_risk_exposure:,.2f}) strictly overrides the structural materiality threshold."
    elif total_risk_exposure > 0:
        return "QUALIFIED OPINION / EMPHASIS OF MATTER: Micro-anomalies detected, but not pervasive enough to compromise the entire trial balance matrix. Isolated remediation is highly recommended."
    else:
        return "UNMODIFIED OPINION (Clean): The financial records are free from material misstatements and strictly conform to the accepted auditing frameworks natively mapping cleanly to the initial ledgers."

def build_pdf_report(client_name: str, executive_summary: dict, filepath: str):
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom EFS Brand Styles (Big Four Format)
    title_style = ParagraphStyle(
        'EFS_Title',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor("#04060F"),
        alignment=1, # Center
        spaceAfter=30
    )
    
    subtitle_style = ParagraphStyle(
        'EFS_Subtitle',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor("#C9A84C"), # Gold
        alignment=1,
        spaceAfter=20
    )
    
    body_style = styles['Normal']
    
    story = []
    
    # --- COVER PAGE ---
    story.append(Spacer(1, 100))
    story.append(Paragraph("EVERY FINANCIAL SOLUTIONS", title_style))
    story.append(Paragraph("Master Audit Findings Report", subtitle_style))
    story.append(Spacer(1, 50))
    story.append(Paragraph(f"Client Entity: {client_name}", styles['Heading3']))
    story.append(Paragraph(f"Report Date: {datetime.now().strftime('%B %d, %Y')}", styles['Heading3']))
    story.append(Spacer(1, 100))
    story.append(Paragraph("STRICTLY CONFIDENTIAL", ParagraphStyle('conf', alignment=1, textColor=colors.red)))
    story.append(PageBreak())
    
    # --- EXECUTIVE SUMMARY ---
    story.append(Paragraph("Executive Summary", styles['Heading1']))
    total_exposure = executive_summary.get("total_risk_exposure", 0.0)
    opinion = executive_summary.get("draft_audit_opinion", "Opinion Pending.")
    
    story.append(Paragraph(f"Total Verified Risk Exposure: PKR {total_exposure:,.2f}", styles['Heading2']))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Audit Opinion:", styles['Heading3']))
    story.append(Paragraph(opinion, body_style))
    story.append(Spacer(1, 20))
    
    # --- DETAILED FINDINGS ---
    story.append(Paragraph("Detailed Findings & Anomalies", styles['Heading2']))
    top_flags = executive_summary.get("top_5_flags", [])
    
    if top_flags:
        data = [["Agent Source", "Reasoning & Finding"]]
        for f in top_flags:
            data.append([f.get("agent", "Unknown")[:20], f.get("reasoning", "")[:100] + "..."])
            
        t = Table(data, colWidths=[100, 350])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#04060F")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F5F5F5")),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#C9A84C")),
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No critical findings reported.", body_style))
        
    story.append(Spacer(1, 20))
    
    # --- REGULATORY HEATMAP ---
    story.append(Paragraph("Regulatory Framework Heatmap", styles['Heading2']))
    heatmap = executive_summary.get("regulatory_heatmap", {})
    if heatmap:
        hdata = [["Rule Cited", "Hit Count"]]
        for rule, count in heatmap.items():
            hdata.append([rule, str(count)])
        ht = Table(hdata, colWidths=[350, 100])
        ht.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#04060F")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor("#C9A84C")),
        ]))
        story.append(ht)
    else:
        story.append(Paragraph("No regulatory infractions detected.", body_style))
        
    # --- SIGNATURE ---
    story.append(Spacer(1, 50))
    story.append(Paragraph("Respectfully Submitted,", body_style))
    story.append(Spacer(1, 30))
    story.append(Paragraph("Hamza Moon", styles['Heading3']))
    story.append(Paragraph("Senior Lead Auditor", body_style))
    story.append(Paragraph("Every Financial Solutions", body_style))
    
    doc.build(story)
    return filepath
