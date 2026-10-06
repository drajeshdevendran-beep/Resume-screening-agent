"""
CogniHire — Report Generator Module
Generates downloadable Excel and PDF recruiter reports.
"""
import io
import pandas as pd
from datetime import datetime


def generate_excel_report(candidates: list, job_title: str = "") -> bytes:
    """Generate an Excel report for download."""
    output = io.BytesIO()

    report_data = []
    for i, c in enumerate(candidates, 1):
        report_data.append({
            "Rank": i,
            "Candidate Name": c.get("name", ""),
            "Email": c.get("email", ""),
            "Phone": c.get("phone", ""),
            "Skills": c.get("skills", ""),
            "Experience (Years)": c.get("experience_years", 0),
            "Education": c.get("education", ""),
            "Score": c.get("score", 0),
            "Recommendation": c.get("recommendation", ""),
            "Justification": c.get("justification", ""),
        })

    df = pd.DataFrame(report_data)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Candidates")

        worksheet = writer.sheets["Candidates"]
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

    output.seek(0)
    return output.getvalue()


def generate_pdf_report(candidates: list, job_title: str = "") -> bytes:
    """Generate a PDF recruiter report for download."""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import (
        SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    )
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter,
                            rightMargin=0.5*inch, leftMargin=0.5*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)

    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Heading1"],
        fontSize=22, textColor=HexColor("#4F46E5"),
        spaceAfter=6, alignment=1
    )
    elements.append(Paragraph("CogniHire — Recruiter Report", title_style))

    subtitle_style = ParagraphStyle(
        "Subtitle", parent=styles["Normal"],
        fontSize=11, textColor=HexColor("#6B7280"),
        alignment=1, spaceAfter=20
    )
    job_label = job_title if job_title else "All Positions"
    elements.append(Paragraph(f"Position: {job_label}", subtitle_style))
    elements.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        subtitle_style
    ))

    # Disclaimer
    disclaimer_style = ParagraphStyle(
        "Disclaimer", parent=styles["Normal"],
        fontSize=8, textColor=HexColor("#9CA3AF"),
        alignment=1, spaceAfter=20, fontName="Helvetica-Oblique"
    )
    elements.append(Paragraph(
        "This report is an AI-generated recommendation to assist recruiters. "
        "It is not a hiring decision. Final hiring decisions should always involve "
        "human judgment, interviews, and compliance with applicable employment laws.",
        disclaimer_style
    ))

    elements.append(Spacer(1, 0.2*inch))

    # Candidate table
    if candidates:
        table_data = [["Rank", "Name", "Score", "Recommendation", "Key Justification"]]
        for i, c in enumerate(candidates, 1):
            justification = c.get("justification", "")
            if len(justification) > 80:
                justification = justification[:77] + "..."
            table_data.append([
                str(i),
                c.get("name", ""),
                f"{c.get('score', 0)}",
                c.get("recommendation", ""),
                justification
            ])

        col_widths = [0.5*inch, 1.3*inch, 0.6*inch, 1.1*inch, 3.5*inch]
        table = Table(table_data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor("#4F46E5")),
            ("TEXTCOLOR", (0, 0), (-1, 0), HexColor("#FFFFFF")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
            ("TOPPADDING", (0, 0), (-1, 0), 10),
            ("BACKGROUND", (0, 1), (-1, -1), HexColor("#F9FAFB")),
            ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#E5E7EB")),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("TOPPADDING", (0, 1), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("No candidates found.", styles["Normal"]))

    # Footer disclaimer
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(
        "CONFIDENTIAL — For internal recruiting use only. "
        "AI-generated scores are advisory and should not be the sole basis for employment decisions.",
        disclaimer_style
    ))

    doc.build(elements)
    output.seek(0)
    return output.getvalue()
