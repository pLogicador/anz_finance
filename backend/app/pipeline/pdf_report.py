"""PDF export (Fase 7) -- a real report with ANZ's own branding/context
(title, active filters, KPI summary, category breakdown, generation
timestamp), not a raw dump of transaction rows. Uses reportlab (pure
Python, no system binary dependency like wkhtmltopdf/headless-Chrome would
need -- important for a plain `pip install` Railway deploy).
"""

from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from xml.sax.saxutils import escape

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.pipeline.metrics import PeriodSummary

BRAND_DARK = colors.HexColor("#0f172a")
BRAND_ACCENT = colors.HexColor("#0ea5e9")
BORDER = colors.HexColor("#cbd5e1")
HEADER_BG = colors.HexColor("#f1f5f9")


def _format_currency(value: float) -> str:
    negative = value < 0
    text = f"{abs(value):,.2f}"
    text = text.replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{'-' if negative else ''}R$ {text}"


def build_pdf_report(
    *,
    month: str,
    categories: list[str],
    type_filter: str,
    summary: PeriodSummary,
    category_breakdown: pd.DataFrame,
    generated_at: datetime | None = None,
) -> bytes:
    """``month``/``categories``/``type_filter`` come straight from request
    query params (``routes/export.py``) and are never validated against a
    known-good list at this layer -- they're interpolated into a
    ``reportlab.Paragraph``, which parses a small XML-like markup subset
    (``<b>``, ``&nbsp;``, ...). Confirmed by hand that an unescaped,
    unbalanced value (e.g. a query param containing a bare ``<``) raises an
    unhandled ``ValueError`` inside reportlab's own parser -- a crash on
    malformed input, not just a cosmetic markup-injection risk. Every
    interpolated user-controlled string here MUST go through
    ``xml.sax.saxutils.escape`` first; don't add a new f-string into a
    ``Paragraph(...)`` call without it.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("AnzTitle", parent=styles["Title"], textColor=BRAND_DARK, spaceAfter=2)
    subtitle_style = ParagraphStyle("AnzSubtitle", parent=styles["Normal"], textColor=colors.HexColor("#475569"))
    section_style = ParagraphStyle("AnzSection", parent=styles["Heading2"], textColor=BRAND_DARK, spaceBefore=16, spaceAfter=8)
    footer_style = ParagraphStyle("AnzFooter", parent=styles["Normal"], textColor=colors.HexColor("#94a3b8"), fontSize=8)

    elements = [
        Paragraph("ANZ Finance", title_style),
        Paragraph("Relatório financeiro", ParagraphStyle("AnzHeadline", parent=styles["Heading3"], textColor=BRAND_ACCENT)),
        Spacer(1, 6),
        Paragraph(
            f"Período: <b>{escape(month)}</b> &nbsp;·&nbsp; Categorias: <b>{escape('todas' if not categories else ', '.join(categories))}</b> "
            f"&nbsp;·&nbsp; Tipo: <b>{escape(type_filter)}</b>",
            subtitle_style,
        ),
        Spacer(1, 16),
    ]

    kpi_rows = [
        ["Receitas", _format_currency(summary.income)],
        ["Despesas", _format_currency(abs(summary.expense))],
        ["Saldo", _format_currency(summary.net)],
        ["Transações no período", str(summary.transaction_count)],
        ["Maior categoria de gasto", summary.top_category or "-"],
    ]
    kpi_table = Table(kpi_rows, colWidths=[7 * cm, 7 * cm])
    kpi_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), HEADER_BG),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(kpi_table)

    if not category_breakdown.empty:
        elements.append(Paragraph("Gastos por categoria", section_style))
        rows = [["Categoria", "Valor"]] + [[str(r["Categorias"]), _format_currency(float(r["Valor"]))] for _, r in category_breakdown.iterrows()]
        cat_table = Table(rows, colWidths=[9 * cm, 5 * cm])
        cat_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), BRAND_DARK),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HEADER_BG]),
                ]
            )
        )
        elements.append(cat_table)

    timestamp = (generated_at or datetime.now(UTC)).strftime("%d/%m/%Y %H:%M UTC")
    elements.append(Spacer(1, 24))
    elements.append(Paragraph(f"Gerado em {timestamp} a partir dos dados desta sessão · ANZ Finance", footer_style))

    doc.build(elements)
    return buffer.getvalue()
