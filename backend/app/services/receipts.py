"""Generación de recibos PDF (formato 80mm tipo POS)."""
from io import BytesIO
from datetime import datetime
from typing import Optional

from reportlab.lib.pagesizes import mm
from reportlab.lib.units import mm as mm_unit
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import Paragraph

from ..models.pos import Sale
from ..core.config import settings


PAYMENT_LABELS = {
    "cash": "Efectivo",
    "card": "Tarjeta",
    "transfer": "Transferencia",
    "mercadopago": "MercadoPago",
}


def render_sale_receipt(sale: Sale, member_name: Optional[str] = None) -> bytes:
    """Renderiza un recibo POS en formato 80mm de ancho, alto adaptativo."""
    width = 80 * mm_unit
    line_h = 4.2 * mm_unit
    items_count = len(sale.items)
    # Alto estimado: header(50mm) + items + footer(40mm)
    height = (60 + items_count * 5 + 40) * mm_unit

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))

    y = height - 8 * mm_unit
    margin = 4 * mm_unit

    # Header
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(width / 2, y, settings.APP_NAME)
    y -= line_h
    c.setFont("Helvetica", 7)
    c.drawCentredString(width / 2, y, "Recibo de venta")
    y -= line_h * 1.5

    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin, y, f"Recibo Nº: {sale.sale_number}")
    y -= line_h
    c.setFont("Helvetica", 7)
    created = sale.created_at or datetime.utcnow()
    c.drawString(margin, y, f"Fecha: {created.strftime('%d/%m/%Y %H:%M')}")
    y -= line_h
    if member_name:
        c.drawString(margin, y, f"Socio: {member_name}")
        y -= line_h
    if sale.cashier:
        c.drawString(margin, y, f"Atendió: {sale.cashier}")
        y -= line_h

    # Línea separadora
    y -= 1 * mm_unit
    c.line(margin, y, width - margin, y)
    y -= 2 * mm_unit

    # Items
    c.setFont("Helvetica-Bold", 7)
    c.drawString(margin, y, "Cant Descripción")
    c.drawRightString(width - margin, y, "Total")
    y -= line_h
    c.setFont("Helvetica", 7)

    for item in sale.items:
        # Truncar nombre largo
        name = item.product_name[:24]
        c.drawString(margin, y, f"{item.quantity:>2}  {name}")
        c.drawRightString(width - margin, y, f"${item.total:.2f}")
        y -= line_h
        if item.unit_price * item.quantity != item.total or item.discount > 0:
            sub = f"   {item.quantity} x ${item.unit_price:.2f}"
            if item.discount > 0:
                sub += f"  desc: ${item.discount:.2f}"
            c.setFont("Helvetica-Oblique", 6)
            c.drawString(margin, y, sub)
            c.setFont("Helvetica", 7)
            y -= line_h * 0.85

    # Línea
    y -= 1 * mm_unit
    c.line(margin, y, width - margin, y)
    y -= 3 * mm_unit

    # Totales
    c.setFont("Helvetica", 7)
    c.drawString(margin, y, "Subtotal:")
    c.drawRightString(width - margin, y, f"${sale.subtotal:.2f}")
    y -= line_h
    if sale.discount:
        c.drawString(margin, y, "Descuento:")
        c.drawRightString(width - margin, y, f"-${sale.discount:.2f}")
        y -= line_h
    if sale.tax:
        c.drawString(margin, y, "Impuestos:")
        c.drawRightString(width - margin, y, f"${sale.tax:.2f}")
        y -= line_h

    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "TOTAL:")
    c.drawRightString(width - margin, y, f"${sale.total:.2f}")
    y -= line_h * 1.4

    # Pago
    c.setFont("Helvetica", 7)
    payment = PAYMENT_LABELS.get(sale.payment_method, sale.payment_method)
    c.drawString(margin, y, f"Pago: {payment}")
    y -= line_h
    if sale.payment_reference:
        c.drawString(margin, y, f"Ref: {sale.payment_reference}")
        y -= line_h

    # Footer
    y -= line_h
    c.setFont("Helvetica-Oblique", 6)
    c.drawCentredString(width / 2, y, "¡Gracias por tu compra!")
    y -= line_h * 0.8
    c.drawCentredString(width / 2, y, "Conserva este comprobante")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()
