"""Utility script to convert knowledge base text files into PDF documents using reportlab."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def text_file_to_pdf(text_file: Path, pdf_file: Path) -> None:
    """Convert one UTF-8 text file into a simple paginated PDF file."""
    lines = text_file.read_text(encoding="utf-8").splitlines()

    pdf_file.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(pdf_file), pagesize=A4)
    width, height = A4

    x_margin = 50
    y = height - 50
    line_height = 14

    c.setFont("Helvetica", 10)
    for raw_line in lines:
        line = raw_line if raw_line.strip() else " "
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 50
        c.drawString(x_margin, y, line[:130])
        y -= line_height

    c.save()


def convert_all_texts(knowledge_base_dir: str = "knowledge_base") -> None:
    """Convert every .txt file in the knowledge base directory into a sibling .pdf file."""
    kb_path = Path(knowledge_base_dir)
    for txt_path in sorted(kb_path.glob("*.txt")):
        pdf_path = txt_path.with_suffix(".pdf")
        text_file_to_pdf(txt_path, pdf_path)
        print(f"Converted: {txt_path.name} -> {pdf_path.name}")


if __name__ == "__main__":
    convert_all_texts()
