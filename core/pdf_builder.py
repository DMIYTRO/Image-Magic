"""
Ядро генерации PDF отчётов с использованием ReportLab.
"""

import os
from typing import List, Tuple
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from core.inspector import ImageMetadata
from validators.rules import ValidationResult

def build_pdf_report(results: List[Tuple[ImageMetadata, ValidationResult, str]], output_dir: str) -> str:
    """Генерирует многостраничный PDF-отчёт pre-press проверки."""
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, "report.pdf")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Стили текста
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#c02b2b"),
        alignment=1,
        spaceAfter=10
    )

    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#6c757d"),
        alignment=1,
        spaceAfter=20
    )

    h2_style = ParagraphStyle(
        'CardHeader',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#212529"),
        spaceAfter=10
    )

    cell_style = ParagraphStyle('CellText', parent=styles['Normal'], fontSize=9, leading=11)
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold')

    story = []

    # Заголовок отчёта
    story.append(Paragraph("<b>Pre-Press Audit Report</b>", title_style))
    story.append(Paragraph("Image-Magic Pre-Press Inspection & Safe Zone Guidelines Report", subtitle_style))

    for idx, (meta, val, rel_preview) in enumerate(results):
        if idx > 0:
            story.append(PageBreak())

        # Заголовок макета
        story.append(Paragraph(f"<b>Layout #{idx + 1}: {meta.file_name}</b>", h2_style))

        # Превью изображение
        abs_preview = os.path.join(output_dir, rel_preview)
        if os.path.exists(abs_preview):
            try:
                # Масштабирование под A4 (ширина ~450pt)
                img = RLImage(abs_preview, width=420, height=280)
                img.hAlign = 'CENTER'
                story.append(img)
                story.append(Spacer(1, 10))
            except Exception as e:
                story.append(Paragraph(f"Preview unavailable: {e}", subtitle_style))

        # Таблица параметров
        table_data = [
            [
                Paragraph("<b>Parameter</b>", cell_bold),
                Paragraph("<b>Your File</b>", cell_bold),
                Paragraph("<b>Target Norm</b>", cell_bold),
                Paragraph("<b>Status</b>", cell_bold)
            ]
        ]

        for item in val.items:
            status_text = f"<font color='green'><b>PASS</b></font>" if item.passed else f"<font color='red'><b>FAIL ({item.message})</b></font>"
            table_data.append([
                Paragraph(item.name, cell_style),
                Paragraph(item.actual_value, cell_style),
                Paragraph(item.target_value, cell_style),
                Paragraph(status_text, cell_style)
            ])

        t = Table(table_data, colWidths=[160, 110, 110, 140])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#c02b2b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 15))

        # Итоговое вердикт-уведомление
        verdict_color = colors.HexColor("#e8f5e9") if val.overall_passed else colors.HexColor("#fff8f8")
        border_c = colors.HexColor("#28a745") if val.overall_passed else colors.HexColor("#dc3545")
        verdict_msg = (
            "<b>STATUS: PASSED</b> - All pre-press parameters meet required standards."
            if val.overall_passed else
            "<b>STATUS: ACTION REQUIRED</b> - Layout requires pre-press review."
        )

        v_table = Table([[Paragraph(verdict_msg, cell_style)]], colWidths=[520])
        v_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), verdict_color),
            ('BOX', (0, 0), (-1, -1), 1, border_c),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(v_table)

    doc.build(story)
    return pdf_path
