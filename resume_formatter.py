"""Resume formatter: parse structured AI resume output and render styled PDF/DOCX.

The tailoring prompts instruct the model to output a strict structure:
  ALL CAPS name line, tagline, contact line, ## section headers,
  ### Role | Company job headers, *location | dates* meta lines,
  - bullet points, and **bold** labels.

This module parses that structure and renders it with professional
formatting (centered header, styled sections, proper bullets) instead
of the raw text dump the old export produced.
"""

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Parser: structured text -> list of blocks
# ---------------------------------------------------------------------------

def parse_structured_resume(text):
    """Parse structured resume text into a list of content blocks.

    Each block is a dict: {"type": ..., "text": ...}
    Types: name, tagline, contact, section, job, job_meta, bullet, paragraph
    """
    lines = [ln.rstrip() for ln in text.split("\n")]
    # Drop leading/trailing blank lines, collapse 3+ blanks to max 1 separator
    stripped = [ln for ln in lines]
    while stripped and not stripped[0].strip():
        stripped.pop(0)
    while stripped and not stripped[-1].strip():
        stripped.pop()

    blocks = []
    header_lines_seen = 0  # first 3 non-empty lines: name, tagline, contact

    for line in stripped:
        s = line.strip()
        if not s:
            continue

        # Section header: ## TEXT
        if s.startswith("## "):
            blocks.append({"type": "section", "text": s[3:].strip()})
            continue
        # Job header: ### Role | Company
        if s.startswith("### "):
            blocks.append({"type": "job", "text": s[4:].strip()})
            continue
        # Bullet: - text  (also handle * bullets that are not *italic* lines)
        if s.startswith("- ") or s.startswith("\u2022 "):
            blocks.append({"type": "bullet", "text": s[2:].strip()})
            continue
        # Italic meta line: *location | dates*
        if s.startswith("*") and s.endswith("*") and len(s) > 2:
            blocks.append({"type": "job_meta", "text": s[1:-1].strip()})
            continue

        # Header block: first three content lines are name / tagline / contact
        if header_lines_seen < 3 and not any(
            b["type"] in ("section", "job", "job_meta", "bullet") for b in blocks
        ):
            if header_lines_seen == 0:
                blocks.append({"type": "name", "text": s})
            elif header_lines_seen == 1:
                blocks.append({"type": "tagline", "text": s})
            else:
                blocks.append({"type": "contact", "text": s})
            header_lines_seen += 1
            continue

        blocks.append({"type": "paragraph", "text": s})

    return blocks


def _md_bold_to_html(text):
    """Convert **bold** markers to reportlab <b> tags; escape HTML specials."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)


def _split_bold_runs(text):
    """Split text into (segment, bold) tuples on ** markers for python-docx."""
    parts = re.split(r"(\*\*.+?\*\*)", text)
    runs = []
    for p in parts:
        if p.startswith("**") and p.endswith("**"):
            runs.append((p[2:-2], True))
        elif p:
            runs.append((p, False))
    return runs


# ---------------------------------------------------------------------------
# PDF renderer (reportlab)
# ---------------------------------------------------------------------------

def render_pdf(blocks, output_path, candidate_name="", cover_letter_text=""):
    """Render blocks to a styled PDF. Returns the page count."""
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    )
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.colors import HexColor

    gray = HexColor("#555555")
    rule_color = HexColor("#999999")

    styles = {
        "name": ParagraphStyle("Name", fontSize=16, leading=19,
                               alignment=TA_CENTER, fontName="Helvetica-Bold",
                               spaceAfter=4),
        "tagline": ParagraphStyle("Tagline", fontSize=10, leading=13,
                                  alignment=TA_CENTER, fontName="Helvetica-Bold",
                                  spaceAfter=2),
        "contact": ParagraphStyle("Contact", fontSize=9, leading=11,
                                  alignment=TA_CENTER, textColor=gray,
                                  spaceAfter=10),
        "section": ParagraphStyle("Section", fontSize=12, leading=15,
                                  fontName="Helvetica-Bold",
                                  spaceBefore=12, spaceAfter=4),
        "job": ParagraphStyle("Job", fontSize=11, leading=14,
                              fontName="Helvetica-Bold",
                              spaceBefore=8, spaceAfter=2),
        "job_meta": ParagraphStyle("JobMeta", fontSize=10, leading=13,
                                   fontName="Helvetica-Oblique", textColor=gray,
                                   spaceAfter=4),
        "bullet": ParagraphStyle("Bullet", fontSize=10, leading=14,
                                 alignment=TA_LEFT, leftIndent=18,
                                 bulletIndent=8, spaceAfter=3),
        "paragraph": ParagraphStyle("Para", fontSize=10, leading=14,
                                    alignment=TA_LEFT, spaceAfter=6),
        "footer": ParagraphStyle("Footer", fontSize=8, leading=10,
                                 alignment=TA_CENTER, textColor=gray),
    }

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(gray)
        label = f"{candidate_name} | {doc.page}" if candidate_name else str(doc.page)
        canvas.drawCentredString(letter[0] / 2, 0.5 * inch, label)
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(output_path), pagesize=letter,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.6 * inch, bottomMargin=0.7 * inch,
        title=f"Resume - {candidate_name}" if candidate_name else "Resume",
    )

    story = []
    for b in blocks:
        t = b["type"]
        html = _md_bold_to_html(b["text"])
        if t == "name":
            story.append(Paragraph(html, styles["name"]))
        elif t == "tagline":
            story.append(Paragraph(html, styles["tagline"]))
        elif t == "contact":
            story.append(Paragraph(html, styles["contact"]))
        elif t == "section":
            story.append(Paragraph(html, styles["section"]))
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=rule_color, spaceAfter=6))
        elif t == "job":
            story.append(Paragraph(html, styles["job"]))
        elif t == "job_meta":
            story.append(Paragraph(html, styles["job_meta"]))
        elif t == "bullet":
            story.append(Paragraph(html, styles["bullet"], bulletText="\u2022"))
        else:
            story.append(Paragraph(html, styles["paragraph"]))

    # Cover letter on its own section after the resume
    if cover_letter_text and cover_letter_text.strip():
        from reportlab.platypus import PageBreak
        story.append(PageBreak())
        story.append(Paragraph("Cover Letter", styles["section"]))
        story.append(HRFlowable(width="100%", thickness=0.5,
                                color=rule_color, spaceAfter=6))
        for para in cover_letter_text.strip().split("\n"):
            if para.strip():
                story.append(Paragraph(_md_bold_to_html(para.strip()),
                                       styles["paragraph"]))

    page_count = [0]

    def count_pages(canvas, doc):
        page_count[0] = max(page_count[0], doc.page)
        footer(canvas, doc)

    doc.build(story, onFirstPage=count_pages, onLaterPages=count_pages)
    return page_count[0]


# ---------------------------------------------------------------------------
# DOCX renderer (python-docx)
# ---------------------------------------------------------------------------

def render_docx(blocks, output_path, candidate_name="", cover_letter_text=""):
    """Render blocks to a styled Word document."""
    from docx import Document
    from docx.shared import Pt, Inches, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()
    for section in doc.sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.7)
        section.right_margin = Inches(0.7)

    # Footer: NAME | page number
    footer_para = doc.sections[0].footer.paragraphs[0]
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if candidate_name:
        run = footer_para.add_run(f"{candidate_name} | ")
        run.font.size = Pt(8)
        run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    # PAGE field
    fld_char1 = OxmlElement("w:fldChar")
    fld_char1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_char2 = OxmlElement("w:fldChar")
    fld_char2.set(qn("w:fldCharType"), "end")
    run = footer_para.add_run()
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(0x55, 0x55, 0x55)
    run._r.append(fld_char1)
    run._r.append(instr)
    run._r.append(fld_char2)

    def add_styled(text, size, bold=False, italic=False, centered=False,
                   space_after=6, space_before=0, color=None):
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(space_after)
        p.paragraph_format.space_before = Pt(space_before)
        if centered:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for segment, seg_bold in _split_bold_runs(text):
            run = p.add_run(segment)
            run.font.size = Pt(size)
            run.bold = bold or seg_bold
            run.italic = italic
            if color:
                run.font.color.rgb = color
        return p

    def add_section_header(text):
        p = add_styled(text, 12, bold=True, space_before=12, space_after=4)
        # Bottom border under section header
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "6")
        bottom.set(qn("w:color"), "999999")
        pBdr.append(bottom)
        pPr.append(pBdr)
        return p

    gray = RGBColor(0x55, 0x55, 0x55)

    for b in blocks:
        t = b["type"]
        txt = b["text"]
        if t == "name":
            add_styled(txt.upper(), 16, bold=True, centered=True, space_after=4)
        elif t == "tagline":
            add_styled(txt, 10, bold=True, centered=True, space_after=2)
        elif t == "contact":
            add_styled(txt, 9, centered=True, space_after=10, color=gray)
        elif t == "section":
            add_section_header(txt)
        elif t == "job":
            add_styled(txt, 11, bold=True, space_before=8, space_after=2)
        elif t == "job_meta":
            add_styled(txt, 10, italic=True, space_after=4, color=gray)
        elif t == "bullet":
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(3)
            for segment, seg_bold in _split_bold_runs(txt):
                run = p.add_run(segment)
                run.font.size = Pt(10)
                run.bold = seg_bold
        else:
            add_styled(txt, 10, space_after=6)

    # Cover letter after the resume
    if cover_letter_text and cover_letter_text.strip():
        doc.add_page_break()
        add_section_header("Cover Letter")
        for para in cover_letter_text.strip().split("\n"):
            if para.strip():
                add_styled(para.strip(), 10, space_after=6)

    doc.save(str(output_path))


# ---------------------------------------------------------------------------
# Convenience: format the resume portion of tailor output
# ---------------------------------------------------------------------------

def extract_resume_text(tailored_output):
    """Pull the resume text from between the [TAILORING_COMPLETE] and
    [COVER LETTER] delimiters."""
    start = tailored_output.find("[TAILORING_COMPLETE]")
    end = tailored_output.find("[COVER LETTER]")
    if start == -1:
        return tailored_output.strip()
    start += len("[TAILORING_COMPLETE]")
    resume = tailored_output[start:end if end != -1 else len(tailored_output)]
    return resume.strip()


def format_resume_file(input_path, output_path, fmt="pdf", cover_letter_path=None):
    """Read a saved tailored resume text file and write a styled PDF or DOCX.

    Returns (output_path, pdf_page_count or None).
    """
    text = Path(input_path).read_text(encoding="utf-8")
    resume_text = extract_resume_text(text)
    blocks = parse_structured_resume(resume_text)
    name = next((b["text"] for b in blocks if b["type"] == "name"), "")
    cover_letter_text = ""
    if cover_letter_path and Path(cover_letter_path).exists():
        cover_letter_text = Path(cover_letter_path).read_text(encoding="utf-8")
    fmt = fmt.lower().lstrip(".")
    if fmt == "pdf":
        pages = render_pdf(blocks, output_path, candidate_name=name,
                           cover_letter_text=cover_letter_text)
        return str(output_path), pages
    elif fmt in ("docx", "word"):
        render_docx(blocks, output_path, candidate_name=name,
                    cover_letter_text=cover_letter_text)
        return str(output_path), None
    raise ValueError(f"Unsupported format: {fmt}")
