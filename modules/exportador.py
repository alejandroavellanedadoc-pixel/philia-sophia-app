
from __future__ import annotations

from io import BytesIO
import textwrap
import pandas as pd


def df_to_excel_bytes(sheets: dict[str, pd.DataFrame]) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe_name = name[:31].replace("/", "-")
            df.to_excel(writer, index=False, sheet_name=safe_name)
            ws = writer.sheets[safe_name]
            for col in ws.columns:
                max_len = 10
                letter = col[0].column_letter
                for cell in col:
                    value = "" if cell.value is None else str(cell.value)
                    max_len = min(max(max_len, len(value) + 2), 48)
                ws.column_dimensions[letter].width = max_len
    return output.getvalue()


def df_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


def agenda_to_pdf_bytes(title: str, sections: dict[str, pd.DataFrame]) -> bytes | None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfgen import canvas
    except Exception:
        return None

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 2 * cm
    c.setFont("Helvetica-Bold", 15)
    c.drawString(2 * cm, y, title[:90])
    y -= 0.8 * cm
    c.setFont("Helvetica", 9)

    def new_page_if_needed(y_pos, margin=2*cm):
        if y_pos < margin:
            c.showPage()
            c.setFont("Helvetica", 9)
            return height - 2 * cm
        return y_pos

    for section, df in sections.items():
        y = new_page_if_needed(y, 3*cm)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(2 * cm, y, section[:80])
        y -= 0.5 * cm
        c.setFont("Helvetica", 8)
        if df is None or df.empty:
            c.drawString(2 * cm, y, "Sin registros para este período.")
            y -= 0.5 * cm
            continue
        for _, row in df.head(18).iterrows():
            texto = " | ".join([str(v) for v in row.values[:5] if str(v) != "nan"])
            for line in textwrap.wrap(texto, 115):
                y = new_page_if_needed(y)
                c.drawString(2 * cm, y, line)
                y -= 0.33 * cm
            y -= 0.15 * cm
    c.save()
    return buffer.getvalue()
