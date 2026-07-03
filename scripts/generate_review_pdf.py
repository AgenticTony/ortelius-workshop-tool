"""Generate a styled PDF from mohand-review.md using the project's reportlab setup."""

import re
from pathlib import Path

from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    HRFlowable,
)

# Same colour palette as the project's pdf_service.py
NAVY = HexColor("#0f2b46")
DARK_BLUE = HexColor("#1a365d")
MEDIUM_BLUE = HexColor("#2c5282")
ACCENT_BLUE = HexColor("#3182ce")
LIGHT_BLUE = HexColor("#ebf8ff")
LIGHT_GREY = HexColor("#f7fafc")
MID_GREY = HexColor("#a0aec0")
BORDER_GREY = HexColor("#e2e8f0")
TEXT_DARK = HexColor("#1a202c")
TEXT_BODY = HexColor("#2d3748")

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


def _build_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "CoverTitle", parent=base["Title"], fontName="Helvetica-Bold",
            fontSize=28, leading=34, textColor=white, alignment=TA_CENTER, spaceAfter=12,
        ),
        "cover_sub": ParagraphStyle(
            "CoverSub", fontName="Helvetica", fontSize=14, leading=18,
            textColor=HexColor("#90cdf4"), alignment=TA_CENTER, spaceAfter=6,
        ),
        "cover_date": ParagraphStyle(
            "CoverDate", fontName="Helvetica", fontSize=11, leading=14,
            textColor=MID_GREY, alignment=TA_CENTER,
        ),
        "section_heading": ParagraphStyle(
            "SectionHeading", fontName="Helvetica-Bold", fontSize=16, leading=20,
            textColor=DARK_BLUE, spaceBefore=20, spaceAfter=10,
        ),
        "sub_heading": ParagraphStyle(
            "SubHeading", fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=MEDIUM_BLUE, spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body", fontName="Helvetica", fontSize=10, leading=15,
            textColor=TEXT_BODY, spaceAfter=3,
        ),
        "body_bold": ParagraphStyle(
            "BodyBold", fontName="Helvetica-Bold", fontSize=10, leading=15,
            textColor=TEXT_DARK, spaceAfter=3,
        ),
        "bullet": ParagraphStyle(
            "Bullet", fontName="Helvetica", fontSize=10, leading=15,
            textColor=TEXT_BODY, leftIndent=18, bulletIndent=6, spaceAfter=3,
        ),
        "table_header": ParagraphStyle(
            "TableHeader", fontName="Helvetica-Bold", fontSize=8, leading=11,
            textColor=white,
        ),
        "table_cell": ParagraphStyle(
            "TableCell", fontName="Helvetica", fontSize=8, leading=11,
            textColor=TEXT_BODY,
        ),
        "table_cell_bold": ParagraphStyle(
            "TableCellBold", fontName="Helvetica-Bold", fontSize=8, leading=11,
            textColor=TEXT_DARK,
        ),
        "code": ParagraphStyle(
            "Code", fontName="Courier", fontSize=9, leading=13,
            textColor=HexColor("#2d3748"), leftIndent=18, spaceAfter=2,
        ),
        "footer": ParagraphStyle(
            "Footer", fontName="Helvetica", fontSize=8, leading=10,
            textColor=MID_GREY,
        ),
    }


def _cover_page(canvas, _doc):
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, PAGE_H * 0.38, PAGE_W, 4, fill=1, stroke=0)
    canvas.restoreState()


def _header_footer(canvas, doc):
    canvas.saveState()
    page_num = doc.page
    if page_num == 1:
        canvas.restoreState()
        return
    canvas.setFillColor(white)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setStrokeColor(ACCENT_BLUE)
    canvas.setLineWidth(2)
    canvas.line(MARGIN, PAGE_H - MARGIN + 4 * mm, PAGE_W - MARGIN, PAGE_H - MARGIN + 4 * mm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GREY)
    canvas.drawString(MARGIN, PAGE_H - MARGIN + 6 * mm, "API & Architecture Review")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 6 * mm, "Ortelius Project 5")
    canvas.setStrokeColor(BORDER_GREY)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, MARGIN - 6 * mm, PAGE_W - MARGIN, MARGIN - 6 * mm)
    canvas.drawCentredString(PAGE_W / 2, MARGIN - 12 * mm, f"Page {page_num - 1}")
    canvas.restoreState()


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _build_decisions_table(styles: dict) -> list:
    decisions = [
        ("1", "Join session — how to send the name",
         "api-contract: query param ?name=Anna. Your PDF: body {\"name\": \"Anna\"}",
         "Query param — simpler", "Body JSON — more RESTful, easier to extend later"),
        ("2", "Join session — what comes back",
         "api-contract: full session object. Your PDF: just {\"participant_id\": \"uuid\"}",
         "Full session object", "Participant ID only — lighter"),
        ("3", "Access codes",
         "Your PDF has access_code: \"ABCD12\" on session creation. api-contract doesn't.",
         "Add them — nice for demo", "Skip for now, use session ID"),
        ("4", "GET analysis endpoint",
         "Your PDF has GET /sessions/{id}/analysis. api-contract doesn't.",
         "Add it — fetch without re-running", "Skip — cache the POST response"),
        ("5", "POST /analyse — sync or async?",
         "api-contract: returns full result. Your PDF: returns {\"status\": \"processing\"} then fetch later",
         "Synchronous — simpler code", "Async — better for big sessions"),
        ("6", "Idea category field",
         "Your PDF has \"category\": \"strength\" on ideas. api-contract doesn't.",
         "Drop it — AI categorises later", "Keep it — participants pre-tag"),
        ("7", "Where analysis lives",
         "Your PDF: Firebase /analysis/latest. api-contract: PostgreSQL.",
         "PostgreSQL only — one truth", "Both — Firebase + PostgreSQL"),
        ("8", "QR codes",
         "Your PDF has qr_service.py in the backend.",
         "Frontend generates QR", "Backend returns QR image"),
        ("9", "Firestore service layer",
         "Your PDF has firestore_service.py. api-contract reads directly.",
         "Keep it simple — read directly", "Service layer for separation"),
        ("10", "Backend folder name",
         "Your PDF says backend_fastapi/. api-contract says backend/.",
         "backend/", "backend_fastapi/"),
    ]

    header = [
        Paragraph(_esc("#"), styles["table_header"]),
        Paragraph(_esc("Area"), styles["table_header"]),
        Paragraph(_esc("Where they disagree"), styles["table_header"]),
        Paragraph(_esc("A"), styles["table_header"]),
        Paragraph(_esc("B"), styles["table_header"]),
        Paragraph(_esc("Pick"), styles["table_header"]),
    ]

    data = [header]
    for num, area, conflict, opt_a, opt_b in decisions:
        data.append([
            Paragraph(_esc(num), styles["table_cell_bold"]),
            Paragraph(_esc(area), styles["table_cell_bold"]),
            Paragraph(_esc(conflict), styles["table_cell"]),
            Paragraph(_esc(opt_a), styles["table_cell"]),
            Paragraph(_esc(opt_b), styles["table_cell"]),
            Paragraph("[ ]", styles["table_cell"]),
        ])

    col_widths = [0.8 * cm, 3.2 * cm, 4.8 * cm, 3.5 * cm, 3.5 * cm, 1.2 * cm]

    table = Table(data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
    ]
    for i in range(1, len(data)):
        bg = LIGHT_GREY if i % 2 == 0 else white
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

    table.setStyle(TableStyle(style_cmds))
    return [table]


def _build_endpoints_table(styles: dict, title: str, rows: list[tuple]) -> list:
    elements = []
    elements.append(Paragraph(title, styles["sub_heading"]))

    header = [
        Paragraph(_esc("Method"), styles["table_header"]),
        Paragraph(_esc("Path"), styles["table_header"]),
        Paragraph(_esc("What it does"), styles["table_header"]),
        Paragraph(_esc("Why"), styles["table_header"]),
    ]
    data = [header]
    for method, path, what, why in rows:
        data.append([
            Paragraph(_esc(method), styles["table_cell_bold"]),
            Paragraph(_esc(path), styles["table_cell"]),
            Paragraph(_esc(what), styles["table_cell"]),
            Paragraph(_esc(why), styles["table_cell"]),
        ])

    col_widths = [1.8 * cm, 4 * cm, 4.5 * cm, 6.7 * cm]
    table = Table(data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("BACKGROUND", (0, 0), (-1, 0), MEDIUM_BLUE),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
    ]
    for i in range(1, len(data)):
        bg = LIGHT_GREY if i % 2 == 0 else white
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))

    table.setStyle(TableStyle(style_cmds))
    elements.append(table)
    elements.append(Spacer(1, 0.5 * cm))
    return elements


def generate_review_pdf(output_path: str):
    buffer_or_path = output_path
    styles = _build_styles()

    frame = Frame(MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN, id="main")
    cover_template = PageTemplate(id="cover", frames=[frame], onPage=_cover_page)
    content_template = PageTemplate(id="content", frames=[frame], onPage=_header_footer)

    doc = BaseDocTemplate(buffer_or_path, pagesize=A4)
    doc.addPageTemplates([cover_template, content_template])

    elements = []

    # ── Cover ──
    elements.append(Spacer(1, PAGE_H * 0.28))
    elements.append(Paragraph("Stuff We Need to Agree On", styles["cover_title"]))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph("API &amp; Architecture Review for Mohand", styles["cover_sub"]))
    elements.append(Spacer(1, 2 * cm))
    elements.append(HRFlowable(width="40%", thickness=1, color=MID_GREY, spaceAfter=12, hAlign="CENTER"))
    elements.append(Paragraph("Ortelius Project 5 — Week 1", styles["cover_date"]))
    from reportlab.platypus.doctemplate import NextPageTemplate
    elements.append(NextPageTemplate("content"))
    elements.append(PageBreak())

    # ── Intro ──
    elements.append(Paragraph("Hej Mohand", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "Jag har gått igenom din PDF, api-contract.md och backend.md. "
        "Det finns några ställen där de inte stämmer överens. "
        "Låt oss reda ut dessa innan någon av oss bygger vidare.",
        styles["body"],
    ))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(
        "Kryssa i det alternativ du föredrar för varje rad. "
        "När vi är överens blir api-contract.md den slutgiltiga källan.",
        styles["body"],
    ))

    # ── Decisions table ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Open Questions", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))
    elements.extend(_build_decisions_table(styles))

    # ── Already agreed ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Already on the Same Page", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor("#38a169"), spaceAfter=12))

    agreed = [
        "Hybrid setup — PostgreSQL (Supabase) + Firebase",
        "Real-time idea input via Firestore",
        "Backend calls Claude for analysis, stores result in PostgreSQL",
        "PDF generation on the backend, binary download",
        "Every clustered idea traces back to the person who wrote it",
        "SWOT, PESTEL, custom frameworks",
        "Riverpod for state management",
        "Anonymous Firebase auth — no accounts for participants",
    ]
    for item in agreed:
        elements.append(Paragraph(f"• {item}", styles["bullet"]))

    # ── Backend endpoints ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Backend Endpoints I'm Planning", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "Här är vad jag tänker för API — det här borde ge dig en tydlig bild av vad din Flutter-app anropar och varför.",
        styles["body"],
    ))
    elements.append(Spacer(1, 0.3 * cm))

    elements.extend(_build_endpoints_table(styles, "Sessions", [
        ("POST", "/sessions", "Creates a workshop session", "Facilitator starts a workshop"),
        ("GET", "/sessions/{id}", "Gets session details", "Facilitator dashboard needs this"),
        ("POST", "/sessions/{id}/join", "Participant joins with name", "No accounts — just a name"),
    ]))

    elements.extend(_build_endpoints_table(styles, "Ideas", [
        ("POST", "/sessions/{id}/ideas", "Submit an idea (testing)", "Test backend without Flutter. In prod, Flutter writes to Firestore."),
        ("GET", "/sessions/{id}/ideas", "List all ideas", "Backend needs these before sending to Claude"),
    ]))

    elements.extend(_build_endpoints_table(styles, "Analysis", [
        ("POST", "/sessions/{id}/analyse", "Runs AI analysis", "Reads ideas → sends to Claude → returns SWOT/PESTEL"),
        ("GET", "/sessions/{id}/report", "Downloads PDF report", "Consultant-ready PDF"),
    ]))

    elements.extend(_build_endpoints_table(styles, "Utility", [
        ("GET", "/health", "Health check", "Confirms backend is alive"),
        ("GET", "/docs", "Swagger UI", "Test every endpoint in browser"),
    ]))

    # ── Flow diagram ──
    elements.append(Paragraph("The Flow", styles["sub_heading"]))
    flow_lines = [
        "Flutter → POST /sessions              (create workshop)",
        "Flutter → POST /sessions/{id}/join    (participant joins)",
        "Flutter → Firestore                   (real-time idea input + voting)",
        "Flutter → POST /sessions/{id}/analyse (trigger AI — backend reads from Firestore)",
        "Flutter → GET /sessions/{id}/report   (download PDF)",
    ]
    for line in flow_lines:
        elements.append(Paragraph(_esc(line), styles["code"]))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(
        "Flutter kommunicerar bara med backend för att skapa sessioner, ansluta, analysera och skapa PDF. "
        "Idéinmatning går direkt till Firestore — backend är inte involverad i den delen.",
        styles["body"],
    ))

    # ── What Mohand builds ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("What Your Frontend Needs to Do", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=HexColor("#d69e2e"), spaceAfter=12))
    elements.append(Paragraph("När vi väl är överens om ovanstående:", styles["body"]))
    elements.append(Spacer(1, 0.2 * cm))

    tasks = [
        ('<b>Create session</b> — POST /sessions with {"topic": "...", "framework": "swot"}',),
        ('<b>Join session</b> — POST /sessions/{id}/join (format depends on decision 1)',),
        ('<b>Write ideas to Firestore</b> — sessions/{session_id}/ideas/{idea_id} with participant_id, participant_name, content, votes',),
        ('<b>Trigger analysis</b> — POST /sessions/{id}/analyse (backend reads from Firestore, calls Claude, returns result)',),
        ('<b>Download PDF</b> — GET /sessions/{id}/report (returns application/pdf)',),
        ('<b>Display analysis</b> — render the AnalysisResult JSON in Flutter UI',),
    ]
    for task in tasks:
        elements.append(Paragraph(f"• {task[0]}", styles["bullet"]))

    doc.build(elements)
    print(f"PDF saved to: {output_path}")


if __name__ == "__main__":
    output = str(Path(__file__).parent.parent / "docs" / "mohand-review.pdf")
    generate_review_pdf(output)
