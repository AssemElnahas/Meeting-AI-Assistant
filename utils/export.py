"""
Export meeting summary to PDF.
Requires reportlab.
"""
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from typing import Dict

def export_to_pdf(summary_data: Dict, filename: str = "meeting_summary.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    
    story = []
    
    # Title
    title = Paragraph("Meeting Summary", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Short summary
    p = Paragraph(f"<b>Short Summary:</b><br/>{summary_data.get('short_summary', '')}", styles['Normal'])
    story.append(p)
    story.append(Spacer(1, 12))
    
    # Actions
    actions = "<br/>".join([f"&bull; {a}" for a in summary_data.get('action_items', [])])
    p = Paragraph(f"<b>Action Items:</b><br/>{actions}", styles['Normal'])
    story.append(p)
    
    doc.build(story)
    print(f"PDF exported to {filename}")

