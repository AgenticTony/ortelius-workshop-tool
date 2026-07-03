"""Generate the final project spec PDF using the project's reportlab setup."""

from datetime import datetime
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
    KeepTogether,
)
from reportlab.platypus.doctemplate import NextPageTemplate

# Same colour palette as pdf_service.py
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
GREEN_ACCENT = HexColor("#38a169")
YELLOW_ACCENT = HexColor("#d69e2e")

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
        "code": ParagraphStyle(
            "Code", fontName="Courier", fontSize=8.5, leading=12,
            textColor=HexColor("#2d3748"), leftIndent=18, spaceAfter=2,
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
    canvas.drawString(MARGIN, PAGE_H - MARGIN + 6 * mm, "Ortelius Workshop Tool — Project Spec")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 6 * mm, "Final Agreed Version")
    canvas.setStrokeColor(BORDER_GREY)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, MARGIN - 6 * mm, PAGE_W - MARGIN, MARGIN - 6 * mm)
    canvas.drawCentredString(PAGE_W / 2, MARGIN - 12 * mm, f"Page {page_num - 1}")
    canvas.restoreState()


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _make_table(styles, headers, rows, col_widths, header_bg=NAVY):
    header_row = [Paragraph(_esc(h), styles["table_header"]) for h in headers]
    data = [header_row]
    for row in rows:
        data.append([Paragraph(_esc(str(c)), styles["table_cell"]) for c in row])

    table = Table(data, colWidths=col_widths, hAlign="LEFT", repeatRows=1)
    style_cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
    ]
    for i in range(1, len(data)):
        bg = LIGHT_GREY if i % 2 == 0 else white
        style_cmds.append(("BACKGROUND", (0, i), (-1, i), bg))
    table.setStyle(TableStyle(style_cmds))
    return table


def generate_final_pdf(output_path: str):
    styles = _build_styles()

    frame = Frame(MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN, id="main")
    cover_template = PageTemplate(id="cover", frames=[frame], onPage=_cover_page)
    content_template = PageTemplate(id="content", frames=[frame], onPage=_header_footer)

    doc = BaseDocTemplate(output_path, pagesize=A4)
    doc.addPageTemplates([cover_template, content_template])

    elements = []
    full_w = PAGE_W - 2 * MARGIN

    # ── COVER ──
    elements.append(Spacer(1, PAGE_H * 0.25))
    elements.append(Paragraph("Ortelius Workshop Tool", styles["cover_title"]))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph("Project Specification", styles["cover_sub"]))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Final Agreed Version — Anthony &amp; Mohand", styles["cover_sub"]))
    elements.append(Spacer(1, 2 * cm))
    elements.append(HRFlowable(width="40%", thickness=1, color=MID_GREY, spaceAfter=12, hAlign="CENTER"))
    elements.append(Paragraph(datetime.now().strftime("%B %d, %Y"), styles["cover_date"]))
    elements.append(NextPageTemplate("content"))
    elements.append(PageBreak())

    # ── WHAT WE'RE BUILDING ──
    elements.append(Paragraph("What We're Building", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))
    elements.append(Paragraph(
        "A workshop facilitation tool where a consultant runs a session, participants submit ideas live, "
        "AI clusters and summarises them, and a PDF report is generated. Built for Ortelius consultants "
        "to use in real workshops.",
        styles["body"],
    ))
    elements.append(Spacer(1, 0.3 * cm))

    elements.append(Paragraph("The Flow", styles["sub_heading"]))
    flow_steps = [
        "Facilitator creates a session (picks topic + framework)",
        "Participants join with just a name — no accounts",
        "Participants submit ideas in real-time",
        "Facilitator triggers AI analysis",
        "Claude groups ideas into SWOT/PESTEL categories",
        "PDF report is generated for download",
    ]
    for i, step in enumerate(flow_steps, 1):
        elements.append(Paragraph(f"<b>{i}.</b> {_esc(step)}", styles["bullet"]))

    # ── ARCHITECTURE ──
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Architecture", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))

    arch_lines = [
        "Flutter app       --realtime-->  Firebase Firestore (ideas, votes)",
        "Flutter app       --REST------>  FastAPI backend (sessions, analysis, PDF)",
        "FastAPI backend   --reads---->  Firebase Firestore (ideas for analysis)",
        "FastAPI backend   --calls---->  Claude API (clustering + summarisation)",
        "FastAPI backend   --stores--->  PostgreSQL / Supabase (sessions, analysis, reports)",
    ]
    for line in arch_lines:
        elements.append(Paragraph(_esc(line), styles["code"]))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph(
        "<b>Why hybrid (Firestore + PostgreSQL):</b> Firestore handles real-time — ideas, votes, live "
        "updates during the workshop. PostgreSQL handles persistence — sessions, analysis results, PDF "
        "reports, structured queries. Firestore charges per read/write, PostgreSQL is fixed cost.",
        styles["body"],
    ))

    # ── RESPONSIBILITIES ──
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Responsibilities", styles["sub_heading"]))
    elements.append(_make_table(styles,
        ["Layer", "What it does"],
        [
            ("Flutter", "UI, real-time idea sync, voting, QR code generation"),
            ("Firebase Firestore", "Live workshop data (ideas, votes, participants)"),
            ("Firebase Auth", "Anonymous auth — participants don't create accounts"),
            ("FastAPI", "Session management, AI analysis, PDF generation"),
            ("Claude API", "Idea clustering + summarisation"),
            ("PostgreSQL (Supabase)", "Sessions, analysis results, reports"),
            ("ReportLab", "PDF generation"),
        ],
        [4 * cm, full_w - 4 * cm],
        header_bg=MEDIUM_BLUE,
    ))

    # ── TECH STACK ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Tech Stack", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))
    elements.append(_make_table(styles,
        ["Area", "Choice"],
        [
            ("Frontend", "Flutter (web + mobile)"),
            ("State management", "Riverpod"),
            ("Real-time database", "Firebase Firestore"),
            ("Backend", "FastAPI (Python)"),
            ("AI", "Anthropic Claude API"),
            ("PDF", "ReportLab"),
            ("Auth", "Firebase Anonymous Auth"),
            ("Persistence", "PostgreSQL (Supabase)"),
            ("Hosting", "Firebase Hosting + Render/Railway (or Azure)"),
        ],
        [4 * cm, full_w - 4 * cm],
        header_bg=MEDIUM_BLUE,
    ))

    # ── API ENDPOINTS ──
    elements.append(PageBreak())
    elements.append(Paragraph("API Endpoints", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))

    elements.append(Paragraph("Sessions", styles["sub_heading"]))
    elements.append(_make_table(styles,
        ["Method", "Path", "What it does"],
        [
            ("POST", "/sessions", "Creates a workshop session"),
            ("GET", "/sessions/{id}", "Gets session details"),
            ("POST", "/sessions/{id}/join?name=...", "Participant joins with name (query param)"),
        ],
        [2 * cm, 5.5 * cm, full_w - 7.5 * cm],
        header_bg=MEDIUM_BLUE,
    ))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Ideas", styles["sub_heading"]))
    elements.append(_make_table(styles,
        ["Method", "Path", "What it does"],
        [
            ("POST", "/sessions/{id}/ideas", "Submit an idea (testing only)"),
            ("GET", "/sessions/{id}/ideas", "List all ideas"),
        ],
        [2 * cm, 5.5 * cm, full_w - 7.5 * cm],
        header_bg=MEDIUM_BLUE,
    ))
    elements.append(Paragraph(
        "In production, Flutter writes ideas directly to Firestore. The POST endpoint is for backend testing.",
        styles["body"],
    ))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Analysis", styles["sub_heading"]))
    elements.append(_make_table(styles,
        ["Method", "Path", "What it does"],
        [
            ("POST", "/sessions/{id}/analyse", "Runs AI analysis (synchronous — returns result directly)"),
            ("GET", "/sessions/{id}/analysis", "Fetches stored analysis (refresh without re-running)"),
            ("GET", "/sessions/{id}/report", "Downloads PDF report"),
        ],
        [2 * cm, 5.5 * cm, full_w - 7.5 * cm],
        header_bg=MEDIUM_BLUE,
    ))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Utility", styles["sub_heading"]))
    elements.append(_make_table(styles,
        ["Method", "Path", "What it does"],
        [
            ("GET", "/health", "Confirms backend is running"),
            ("GET", "/docs", "Swagger UI — test everything in browser"),
        ],
        [2 * cm, 5.5 * cm, full_w - 7.5 * cm],
        header_bg=MEDIUM_BLUE,
    ))

    # ── DATA MODELS ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Data Models", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))

    models = [
        ("Session", ['"id": "uuid"', '"topic": "Improve onboarding"', '"framework": "swot"', '"access_code": "ABCD12"', '"status": "active"', '"created_at": "ISO 8601"']),
        ("Participant", ['"id": "uuid"', '"name": "Anna"', '"joined_at": "ISO 8601"']),
        ("Idea", ['"id": "uuid"', '"session_id": "uuid"', '"participant_id": "uuid"', '"participant_name": "Anna"', '"category": "strength" (optional)', '"content": "Better documentation for new hires"', '"votes": 3', '"created_at": "ISO 8601"']),
    ]

    for model_name, fields in models:
        elements.append(Paragraph(model_name, styles["sub_heading"]))
        elements.append(Paragraph("{", styles["code"]))
        for field in fields:
            elements.append(Paragraph(f'  {_esc(field)},', styles["code"]))
        elements.append(Paragraph("}", styles["code"]))
        elements.append(Spacer(1, 0.2 * cm))

    elements.append(Paragraph(
        'Category field on ideas is optional — participants can pre-tag ideas, but AI will categorise '
        'everything during analysis regardless.',
        styles["body"],
    ))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Analysis Result", styles["sub_heading"]))
    analysis_fields = [
        '"session_id": "uuid"',
        '"framework": "swot"',
        '"categories": { strengths: [...], weaknesses: [...], opportunities: [...], threats: [...] }',
        '"key_themes": ["string"]',
        '"decisions_made": ["string"]',
        '"open_questions": ["string"]',
        '"recommended_next_steps": ["string"]',
    ]
    elements.append(Paragraph("{", styles["code"]))
    for field in analysis_fields:
        elements.append(Paragraph(f'  {_esc(field)},', styles["code"]))
    elements.append(Paragraph("}", styles["code"]))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(
        "Every clustered idea references the original idea_id — provenance requirement from Ortelius. "
        "The PDF shows who said what.",
        styles["body"],
    ))

    # ── FIREBASE STRUCTURE ──
    elements.append(PageBreak())
    elements.append(Paragraph("Firebase Firestore Structure", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))

    fs_lines = [
        "sessions/{session_id}/",
        "  +-- topic: string",
        "  +-- framework: string",
        "  +-- status: string",
        "  +-- participants: array",
        "",
        "sessions/{session_id}/ideas/{idea_id}",
        "  +-- participant_id: string",
        "  +-- participant_name: string",
        "  +-- category: string (optional)",
        "  +-- content: string",
        "  +-- votes: number",
        "  +-- created_at: timestamp",
    ]
    for line in fs_lines:
        elements.append(Paragraph(_esc(line), styles["code"]))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Firestore Security Rules", styles["sub_heading"]))
    rules = [
        "Users can only edit their own ideas",
        "Authenticated anonymous users only",
        "Analysis writable only by backend",
    ]
    for rule in rules:
        elements.append(Paragraph(f"• {_esc(rule)}", styles["bullet"]))

    # ── WHAT FLUTTER CALLS ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("What Flutter Calls", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))

    flutter_calls = [
        "Flutter -> POST /sessions              (create workshop)",
        "Flutter -> POST /sessions/{id}/join    (participant joins)",
        "Flutter -> Firestore                   (real-time idea input + voting)",
        "Flutter -> POST /sessions/{id}/analyse (trigger AI)",
        "Flutter -> GET /sessions/{id}/analysis (fetch results)",
        "Flutter -> GET /sessions/{id}/report   (download PDF)",
    ]
    for line in flutter_calls:
        elements.append(Paragraph(_esc(line), styles["code"]))

    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(
        "Flutter generates QR codes locally — it's just encoding a URL, no backend needed.",
        styles["body"],
    ))

    # ── REPO STRUCTURE ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Repo Structure", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))

    repo_lines = [
        "workshopstodverktyg/",
        "+-- backend/                  <-- FastAPI (Anthony)",
        "|   +-- app/",
        "|       +-- main.py",
        "|       +-- config/",
        "|       +-- models/",
        "|       +-- routes/",
        "|       +-- services/",
        "|       |   +-- claude_service.py",
        "|       |   +-- firestore_service.py",
        "|       |   +-- pdf_service.py",
        "|       |   +-- analysis_service.py",
        "|       +-- prompts/",
        "+-- frontend_flutter/         <-- Flutter (Mohand)",
        "|   +-- lib/",
        "|       +-- main.dart",
        "|       +-- core/",
        "|       +-- models/",
        "|       +-- services/",
        "|       +-- features/",
        "|       |   +-- session/",
        "|       |   +-- workshop/",
        "|       |   +-- analysis/",
        "|       |   +-- report/",
        "|       +-- widgets/",
        "+-- firebase/",
        "+-- docs/",
        "+-- README.md",
    ]
    for line in repo_lines:
        elements.append(Paragraph(_esc(line), styles["code"]))

    # ── DEVELOPMENT PHASES ──
    elements.append(PageBreak())
    elements.append(Paragraph("Development Phases", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))

    phases = [
        ("Phase 1 — Workshop Setup", "Weeks 1–2", [
            "Create session", "Join session with name", "Access code generation",
            "QR code generation (frontend)", "Basic real-time dashboard",
        ]),
        ("Phase 2 — Realtime Workshop", "Weeks 3–4", [
            "Submit ideas to Firestore", "Real-time dashboard updates",
            "Upvote ideas", "Facilitator dashboard",
        ]),
        ("Phase 3 — AI Analysis", "Weeks 5–6", [
            "Claude integration", "SWOT/PESTEL clustering",
            "Structured JSON output", "Prompt design + evaluation",
        ]),
        ("Phase 4 — Reports", "Weeks 7–8", [
            "PDF generation (ReportLab)", "Consultant-ready template", "Download flow",
        ]),
        ("Phase 5 — Testing &amp; Polish", "Weeks 9–10", [
            "Multi-participant testing", "Real-time sync stress tests",
            "Error handling", "User testing with Ortelius consultants",
        ]),
        ("Phase 6 — Delivery", "Weeks 11–12", [
            "Cloud deployment", "Documentation", "Demo prep", "Final presentation",
        ]),
    ]

    for phase_name, timing, items in phases:
        elements.append(Paragraph(phase_name, styles["sub_heading"]))
        elements.append(Paragraph(f"<i>{timing}</i>", styles["body"]))
        for item in items:
            elements.append(Paragraph(f"• {_esc(item)}", styles["bullet"]))
        elements.append(Spacer(1, 0.2 * cm))

    # ── CLAUDE PROMPT STRATEGY ──
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("Claude Prompt Strategy", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))
    elements.append(Paragraph("Keep it simple. No agents, no LangChain, no RAG.", styles["body"]))
    elements.append(Spacer(1, 0.2 * cm))

    prompt_lines = [
        "You are analysing workshop ideas.",
        "Group the following ideas into SWOT categories.",
        "Return ONLY valid JSON.",
        "Ideas:",
        "{ideas}",
    ]
    for line in prompt_lines:
        elements.append(Paragraph(_esc(line), styles["code"]))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(
        "Prompt versions tracked in prompts/ directory. Each version logged with what changed and accuracy results.",
        styles["body"],
    ))

    # ── SUCCESS CRITERIA ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Success Criteria", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=GREEN_ACCENT, spaceAfter=12))
    criteria = [
        "Workshop setup < 2 minutes",
        "Mobile participation works without install",
        "Real-time updates feel instant",
        "AI groups ideas correctly (≥80% accuracy on eval dataset)",
        "PDF generated < 30 seconds",
        "Consultants can demo it",
    ]
    for c in criteria:
        elements.append(Paragraph(f"• {_esc(c)}", styles["bullet"]))

    # ── ERROR HANDLING ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Error Handling", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=YELLOW_ACCENT, spaceAfter=12))
    elements.append(Paragraph(
        'All errors return {"detail": "error message"} with HTTP status code:',
        styles["body"],
    ))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(_make_table(styles,
        ["Status", "Meaning"],
        [("200", "Success"), ("404", "Session or resource not found"),
         ("422", "Validation error"), ("500", "Server error")],
        [2.5 * cm, full_w - 2.5 * cm],
        header_bg=MEDIUM_BLUE,
    ))

    # ── PHILOSOPHY ──
    elements.append(Spacer(1, 0.5 * cm))
    elements.append(Paragraph("Philosophy", styles["section_heading"]))
    elements.append(HRFlowable(width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12))

    elements.append(Paragraph("Optimise for:", styles["body_bold"]))
    for item in ["Simplicity", "Maintainability", "Demoability", "Clear documentation"]:
        elements.append(Paragraph(f"• {_esc(item)}", styles["bullet"]))

    elements.append(Spacer(1, 0.3 * cm))
    elements.append(Paragraph("NOT for:", styles["body_bold"]))
    for item in ["Enterprise scalability", "Microservices", "Complex infrastructure"]:
        elements.append(Paragraph(f"• {_esc(item)}", styles["bullet"]))

    elements.append(Spacer(1, 0.5 * cm))
    elements.append(HRFlowable(width="60%", thickness=1, color=ACCENT_BLUE, spaceAfter=8, hAlign="CENTER"))
    elements.append(Paragraph(
        "<b>The cleanest MVP is the best MVP.</b>",
        ParagraphStyle("PhilCenter", fontName="Helvetica-Bold", fontSize=12,
                       leading=16, textColor=DARK_BLUE, alignment=TA_CENTER),
    ))

    doc.build(elements)
    print(f"PDF saved to: {output_path}")


if __name__ == "__main__":
    output = str(Path(__file__).parent.parent / "docs" / "project-final.pdf")
    generate_final_pdf(output)
