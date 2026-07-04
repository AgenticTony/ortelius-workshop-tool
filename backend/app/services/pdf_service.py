from datetime import datetime
from io import BytesIO

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.models import AnalysisResult

# ── Colour palette ──────────────────────────────────────────
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

CATEGORY_COLOURS = [
    {
        "bg": HexColor("#f0fff4"),
        "accent": HexColor("#38a169"),
        "text": HexColor("#22543d"),
    },
    {
        "bg": HexColor("#fff5f5"),
        "accent": HexColor("#e53e3e"),
        "text": HexColor("#742a2a"),
    },
    {
        "bg": HexColor("#ebf8ff"),
        "accent": HexColor("#3182ce"),
        "text": HexColor("#2a4365"),
    },
    {
        "bg": HexColor("#fffff0"),
        "accent": HexColor("#d69e2e"),
        "text": HexColor("#744210"),
    },
    {
        "bg": HexColor("#faf5ff"),
        "accent": HexColor("#805ad5"),
        "text": HexColor("#44337a"),
    },
    {
        "bg": HexColor("#fffaf0"),
        "accent": HexColor("#dd6b20"),
        "text": HexColor("#7b341e"),
    },
    {
        "bg": HexColor("#e6fffa"),
        "accent": HexColor("#319795"),
        "text": HexColor("#234e52"),
    },
    {
        "bg": HexColor("#fff5f7"),
        "accent": HexColor("#d53f8c"),
        "text": HexColor("#702459"),
    },
]

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm


# ── Styles ──────────────────────────────────────────────────
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
        "swot_header": ParagraphStyle(
            "SwotHeader", fontName="Helvetica-Bold", fontSize=11, leading=14,
            textColor=white, alignment=TA_CENTER,
        ),
        "swot_item": ParagraphStyle(
            "SwotItem", fontName="Helvetica", fontSize=9, leading=13,
            textColor=TEXT_BODY, spaceAfter=2,
        ),
        "footer": ParagraphStyle(
            "Footer", fontName="Helvetica", fontSize=8, leading=10,
            textColor=MID_GREY,
        ),
    }


# ── Page templates (header / footer) ────────────────────────
def _header_footer(canvas, doc):
    """Draw header bar and footer on every page except the cover."""
    canvas.saveState()
    page_num = doc.page
    if page_num == 1:
        canvas.restoreState()
        return

    # White background to clear cover page navy
    canvas.setFillColor(white)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)

    # Header — thin accent line
    canvas.setStrokeColor(ACCENT_BLUE)
    canvas.setLineWidth(2)
    canvas.line(MARGIN, PAGE_H - MARGIN + 4 * mm, PAGE_W - MARGIN, PAGE_H - MARGIN + 4 * mm)

    # Header text
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MID_GREY)
    canvas.drawString(MARGIN, PAGE_H - MARGIN + 6 * mm, "Workshop Analysis Report")
    canvas.drawRightString(PAGE_W - MARGIN, PAGE_H - MARGIN + 6 * mm, f"Session: {getattr(doc, '_session_id', 'N/A')}")

    # Footer — page number
    canvas.setStrokeColor(BORDER_GREY)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN, MARGIN - 6 * mm, PAGE_W - MARGIN, MARGIN - 6 * mm)
    canvas.drawCentredString(PAGE_W / 2, MARGIN - 12 * mm, f"Page {page_num - 1}")

    canvas.restoreState()


def _cover_page(canvas, _doc):
    """Draw the cover page background."""
    canvas.saveState()
    # Full navy background
    canvas.setFillColor(NAVY)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    # Accent stripe
    canvas.setFillColor(ACCENT_BLUE)
    canvas.rect(0, PAGE_H * 0.38, PAGE_W, 4, fill=1, stroke=0)
    canvas.restoreState()


# ── Section builders ─────────────────────────────────────────
def _build_cover(styles: dict, analysis: AnalysisResult) -> list:
    elements = []
    elements.append(Spacer(1, PAGE_H * 0.28))
    elements.append(Paragraph("Workshop Analysis Report", styles["cover_title"]))
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(
        f"{analysis.framework.upper()} Framework Analysis",
        styles["cover_sub"],
    ))
    elements.append(Spacer(1, 0.8 * cm))
    elements.append(Paragraph(
        f"Session: {analysis.session_id}",
        styles["cover_sub"],
    ))
    elements.append(Spacer(1, 2 * cm))
    elements.append(HRFlowable(
        width="40%", thickness=1, color=MID_GREY, spaceAfter=12, hAlign="CENTER",
    ))
    elements.append(Paragraph(
        datetime.now().strftime("%B %d, %Y"),
        styles["cover_date"],
    ))
    # Switch template BEFORE the page break
    from reportlab.platypus.doctemplate import NextPageTemplate
    elements.append(NextPageTemplate("content"))
    elements.append(PageBreak())
    return elements


def _build_category_grid(styles: dict, analysis: AnalysisResult) -> list:
    elements = []
    cat_keys = list(analysis.categories.keys())
    if not cat_keys:
        return elements

    framework_label = analysis.framework.upper()
    elements.append(Paragraph(
        f"{framework_label} Analysis", styles["section_heading"],
    ))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=ACCENT_BLUE, spaceAfter=12,
    ))

    num_cols = 2 if len(cat_keys) <= 4 else 3
    col_w = (PAGE_W - 2 * MARGIN - (num_cols - 1) * 0.5 * cm) / num_cols

    def _title_case(key: str) -> str:
        return key.replace("_", " ").title()

    def _cell(key: str, idx: int) -> list:
        colours = CATEGORY_COLOURS[idx % len(CATEGORY_COLOURS)]
        clustered = analysis.categories.get(key, [])
        items = []
        items.append(Paragraph(
            f'<font color="{colours["text"].hexval()}">'
            f"<b>{_title_case(key)}</b></font>",
            styles["sub_heading"],
        ))
        for idea in clustered:
            items.append(Paragraph(
                f'<font color="{colours["text"].hexval()}">'
                f"• {idea.summary}</font>",
                styles["swot_item"],
            ))
        if not clustered:
            items.append(Paragraph(
                f'<font color="{MID_GREY.hexval()}">'
                f"No items identified</font>",
                styles["swot_item"],
            ))
        return items

    rows = []
    for i in range(0, len(cat_keys), num_cols):
        chunk = cat_keys[i : i + num_cols]
        row = [_cell(k, i + j) for j, k in enumerate(chunk)]
        while len(row) < num_cols:
            row.append([])
        rows.append(row)

    grid = Table(rows, colWidths=[col_w] * num_cols, hAlign="CENTER")

    grid_style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 1, BORDER_GREY),
    ]
    for row_idx, row_keys in enumerate(
        range(0, len(cat_keys), num_cols)
    ):
        chunk = cat_keys[row_keys : row_keys + num_cols]
        for col_idx, key in enumerate(chunk):
            colour_idx = row_keys + col_idx
            bg = CATEGORY_COLOURS[colour_idx % len(CATEGORY_COLOURS)]["bg"]
            grid_style.append(
                ("BACKGROUND", (col_idx, row_idx), (col_idx, row_idx), bg)
            )

    grid.setStyle(TableStyle(grid_style))
    elements.append(grid)
    elements.append(Spacer(1, 1 * cm))
    return elements


def _build_section(styles: dict, title: str, items: list[str], accent: HexColor) -> list:
    elements = []
    if not items:
        return elements
    elements.append(Paragraph(title, styles["section_heading"]))
    elements.append(HRFlowable(
        width="100%", thickness=1, color=accent, spaceAfter=8,
    ))
    for item in items:
        elements.append(Paragraph(f"• {item}", styles["bullet"]))
    elements.append(Spacer(1, 0.8 * cm))
    return elements


# ── Main entry point ─────────────────────────────────────────
def generate_pdf(analysis: AnalysisResult) -> bytes:
    """Generate a professional PDF report from analysis results."""
    buffer = BytesIO()

    frame = Frame(MARGIN, MARGIN, PAGE_W - 2 * MARGIN, PAGE_H - 2 * MARGIN, id="main")

    cover_template = PageTemplate(id="cover", frames=[frame], onPage=_cover_page)
    content_template = PageTemplate(id="content", frames=[frame], onPage=_header_footer)

    doc = BaseDocTemplate(buffer, pagesize=A4)
    doc.addPageTemplates([cover_template, content_template])

    styles = _build_styles()
    elements: list = []

    # Cover page (switches to content template internally)
    elements.extend(_build_cover(styles, analysis))

    # Category grid
    elements.extend(_build_category_grid(styles, analysis))

    # Text sections
    elements.extend(_build_section(styles, "Key Themes", analysis.key_themes, ACCENT_BLUE))
    elements.extend(_build_section(styles, "Decisions Made", analysis.decisions_made, HexColor("#38a169")))
    elements.extend(_build_section(styles, "Open Questions", analysis.open_questions, HexColor("#d69e2e")))
    elements.extend(_build_section(styles, "Recommended Next Steps", analysis.recommended_next_steps, MEDIUM_BLUE))

    # Pass session_id for header/footer
    doc._session_id = analysis.session_id
    doc.build(elements)
    return buffer.getvalue()
