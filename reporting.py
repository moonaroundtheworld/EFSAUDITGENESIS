import os
from fpdf import FPDF  # type: ignore
from datetime import datetime

class AuditReportPDF(FPDF):
    def header(self):
        # Big Four styled minimalist layout
        self.set_font('Arial', 'B', 15)
        # EFS brand blue color
        self.set_text_color(0, 51, 102) 
        self.cell(0, 10, 'Every Financial Solutions', 0, 1, 'R')
        
        self.set_text_color(128, 128, 128)
        self.set_font('Arial', 'I', 10)
        self.cell(0, 10, 'Strict & Confidential Audit Deliverable', 0, 1, 'R')
        self.ln(10)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_audit_opinion(total_risk_exposure: float, heatmap: dict, materiality_threshold: float = 1000000.0) -> str:
    """
    NLP Logic block constructing dynamic auditor opinions natively.
    """
    top_rule = None
    if heatmap:
        top_rule = max(heatmap.items(), key=lambda x: x[1])[0]
        
    basis = ""
    if top_rule:
        basis = f" Basis for Opinion: Extensively mapped failures linked explicitly to '{top_rule}'."
        
    if total_risk_exposure > materiality_threshold:
        return f"MODIFIED OPINION (Adverse / Qualified): The financial records present a Material Misstatement.{basis} Verified risk exposure (PKR {total_risk_exposure:,.2f}) strictly overrides the structural materiality threshold."
    elif total_risk_exposure > 0:
        return "QUALIFIED OPINION / EMPHASIS OF MATTER: Micro-anomalies detected, but not pervasive enough to compromise the entire trial balance matrix. Isolated remediation is highly recommended."
    else:
        return "UNMODIFIED OPINION (Clean): The financial records are free from material misstatements and strictly conform to the accepted auditing frameworks natively mapping cleanly to the initial ledgers."

def build_pdf_report(executive_summary: dict, filepath: str):
    pdf = AuditReportPDF()
    pdf.add_page()
    
    client_name = executive_summary.get("client", "Unknown Client")
    total_exposure = executive_summary.get("total_risk_exposure", 0.0)
    top_flags = executive_summary.get("top_5_flags", [])
    
    # Title
    pdf.set_font('Arial', 'B', 20)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 15, 'Master Audit Findings Report', 0, 1, 'C')
    pdf.ln(5)
    
    # Client Info Context
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Client Entity: {client_name}", 0, 1)
    pdf.cell(0, 10, f"Report Date: {datetime.now().strftime('%Y-%m-%d')}", 0, 1)
    
    pdf.ln(5)
    regulatory_heatmap = executive_summary.get("regulatory_heatmap", {})
    opinion = generate_audit_opinion(total_exposure, regulatory_heatmap)
    
    pdf.set_font('Arial', 'B', 14)
    # Red for Modified, Green for Unmodified warning semantics
    if "MODIFIED" in opinion:
        pdf.set_text_color(153, 0, 0)
    else:
        pdf.set_text_color(0, 102, 0)
        
    pdf.cell(0, 10, "Executive Audit Opinion:", 0, 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0, 0, 0) # Reset black text
    pdf.multi_cell(0, 8, opinion)
    pdf.ln(10)
    
    # Total Risk Exposure Matrix
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "Total Verified Risk Exposure", 0, 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"PKR {total_exposure:,.2f}", 0, 1)
    pdf.ln(5)
    
    # Top 5 Critical Vulnerabilities
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "Top 5 Critical Anomalies", 0, 1)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    
    if not top_flags:
        pdf.cell(0, 10, "No critical flags detected mapping against defined matrices.", 0, 1)
    else:
        for idx, flag in enumerate(top_flags):
            agent = flag.get('agent', 'Unknown')
            reasoning = flag.get('reasoning', '')
            pdf.multi_cell(0, 8, f"{idx+1}. [{agent}] {reasoning}")
            pdf.ln(2)
            
    # Regulatory Violations Heatmap Integration
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 10, "Regulatory Framework Violations Heatmap", 0, 1)
    
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(0, 0, 0)
    
    heatmap = executive_summary.get("regulatory_heatmap", {})
    if not heatmap:
        pdf.cell(0, 10, "Zero Internal Regulatory Infractions natively recorded.", 0, 1)
    else:
        for rule, count in heatmap.items():
            pdf.cell(0, 10, f"Hit Count {count}x : {rule}", 0, 1)
            
    pdf.output(filepath)
    return filepath
