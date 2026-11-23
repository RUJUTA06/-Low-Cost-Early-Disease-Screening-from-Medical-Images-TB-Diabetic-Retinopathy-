from io import BytesIO

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from ..schemas import DISCLAIMER


def make_report(case) -> bytes:
    buf = BytesIO()
    pdf = canvas.Canvas(buf, pagesize=letter)
    y = 740
    pdf.setTitle("Screening support review summary")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "Screening Support Review Summary")
    y -= 40
    pdf.setFont("Helvetica", 11)
    fields = [
        ("Case ID", case.id), ("Task", case.task), ("Timestamp (UTC)", str(case.created_at)),
        ("Image quality", f"{case.quality_status}: {', '.join(case.quality_reasons) or 'No quality flags'}"),
        ("Model output", case.output_label), ("Score", str(case.score) if case.score is not None else "Unavailable"),
        ("Confidence", str(case.confidence) if case.confidence is not None else "Unavailable"),
        ("Abstention", case.abstention_reason or ("Yes" if case.abstain else "No")),
        ("Model version", case.model_version), ("Preprocessing version", case.preprocessing_version),
        ("Processing time", f"{case.duration_ms} ms"), ("Review status", case.review_status),
    ]
    for label, value in fields:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(50, y, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(170, y, str(value)[:95])
        y -= 22
    y -= 12
    pdf.setFont("Helvetica-Bold", 11)
    pdf.drawString(50, y, "Safety and interpretation")
    y -= 18
    pdf.setFont("Helvetica", 10)
    for line in [DISCLAIMER[:100], DISCLAIMER[100:200], DISCLAIMER[200:]]:
        if line.strip():
            pdf.drawString(50, y, line)
            y -= 15
    pdf.drawString(50, y - 12, "Explainability, if shown, is a qualitative aid and not a lesion map or medical proof.")
    pdf.save()
    return buf.getvalue()
