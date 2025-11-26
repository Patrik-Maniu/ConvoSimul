#!/usr/bin/env python3
"""
PDF exporter for a conversation (list of {"role": str, "content": str}).

Dependency:
  pip install reportlab
"""

import os
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

try:
    # Python 3.9+: use IANA tz names; default to Europe/Rome per your setup
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None  # Fallback to local time if zoneinfo isn't available


# -------------------- Core PDF building helpers --------------------

def _build_styles():
    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        alignment=TA_LEFT,
        spaceAfter=8,
    )
    role = ParagraphStyle(
        "Role",
        parent=styles["Heading5"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=14,
        spaceBefore=6,
        spaceAfter=2,
    )
    title = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        spaceAfter=12,
    )
    meta = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor="#555555",
        spaceAfter=12,
    )
    return {"body": body, "role": role, "title": title, "meta": meta}


def _add_page_numbers(canvas, doc):
    canvas.saveState()
    page_num = canvas.getPageNumber()
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(doc.rightMargin + doc.width, 1.25 * cm, f"Page {page_num}")
    canvas.restoreState()


def _conversation_to_pdf(messages, output_path, title="Conversation", exported_at_text=None):
    styles = _build_styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title=title,
        author="Conversation Exporter",
        subject="Chat transcript",
    )

    story = []
    story.append(Paragraph(escape(title), styles["title"]))
    if exported_at_text:
        story.append(Paragraph(escape(exported_at_text), styles["meta"]))
    story.append(Spacer(1, 6))

    for msg in messages:
        role_text = str(msg.get("role", "")).strip() or "Unknown"
        content_text = str(msg.get("content", "")).strip()

        story.append(Paragraph(escape(role_text), styles["role"]))
        # Preserve newlines in content
        story.append(Paragraph(escape(content_text).replace("\n", "<br/>"), styles["body"]))

    doc.build(story, onFirstPage=_add_page_numbers, onLaterPages=_add_page_numbers)


# -------------------- Public function to be called --------------------

def export_conversation_to_pdf(messages, output_dir="./outputs/Conversations_PDF/", filename_prefix="", name="output"):
    """
    Create a PDF from `messages` and save it into `output_dir` with a timestamped filename.

    Args:
        messages (list[dict]): Each item must have keys 'role' and 'content'.
        output_dir (str): Directory to write the PDF (default: "./output").
        filename_prefix (str): Optional prefix for the file name (e.g., "chat_").

    Returns:
        str: Absolute path to the created PDF.
    """
    if not isinstance(messages, list) or any(
        not isinstance(m, dict) or "role" not in m or "content" not in m for m in messages
    ):
        raise ValueError("`messages` must be a list of dicts with keys 'role' and 'content'.")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{name}.pdf"
    output_path = os.path.abspath(os.path.join(output_dir, filename))

    title = "Conversation"
    _conversation_to_pdf(messages, output_path, title=title, exported_at_text=f"Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return output_path