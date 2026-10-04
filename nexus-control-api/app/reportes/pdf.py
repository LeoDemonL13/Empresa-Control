import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_LOGO_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
_ROJO = colors.HexColor('#E30613')
_NEGRO = colors.HexColor('#0C0E12')
_GRIS = colors.HexColor('#8A90A0')
_BORDE = colors.HexColor('#D8DADF')
_FILA_ALT = colors.HexColor('#F4F5F7')


def _letterhead():
    logo = Image(_LOGO_PATH, width=14 * mm, height=14 * mm) if os.path.exists(_LOGO_PATH) else ''
    texto = Paragraph(
        '<font color="white" size="15"><b>NEXUS</b> OBSIDIAN</font>'
        '<br/><font color="#8A90A0" size="7">CONTROL &middot; SEC PROTECTED</font>',
        ParagraphStyle('marca', alignment=TA_LEFT, leading=14),
    )
    encabezado = Table([[logo, texto]], colWidths=[20 * mm, None])
    encabezado.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), _NEGRO),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (0, 0), 8),
        ('LEFTPADDING', (1, 0), (1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    barra = Table([['']], colWidths=[None], rowHeights=[2.2 * mm])
    barra.setStyle(TableStyle([('BACKGROUND', (0, 0), (-1, -1), _ROJO)]))
    return [encabezado, barra]


def generar_pdf(titulo: str, subtitulo: str, columnas: list, filas: list, generado_por: str) -> bytes:
    import io

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(letter),
        topMargin=0, bottomMargin=16 * mm, leftMargin=14 * mm, rightMargin=14 * mm,
    )

    elementos = _letterhead()
    elementos.append(Spacer(1, 8 * mm))
    elementos.append(Paragraph(titulo, ParagraphStyle('titulo', fontSize=16, leading=20, textColor=_NEGRO, fontName='Helvetica-Bold')))
    if subtitulo:
        elementos.append(Paragraph(subtitulo, ParagraphStyle('subtitulo', fontSize=10, textColor=_GRIS, spaceBefore=2)))
    meta = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} por {generado_por}"
    elementos.append(Paragraph(meta, ParagraphStyle('meta', fontSize=8, textColor=_GRIS, spaceBefore=2)))
    elementos.append(Spacer(1, 6 * mm))

    if filas:
        estilo_celda = ParagraphStyle('celda', fontSize=8, leading=10, textColor=_NEGRO)
        estilo_encabezado = ParagraphStyle('encabezado_celda', fontSize=8, leading=10, textColor=colors.white, fontName='Helvetica-Bold')
        filas_envueltas = [[Paragraph(str(c), estilo_encabezado) for c in columnas]]
        for fila in filas:
            filas_envueltas.append([Paragraph(str(c), estilo_celda) for c in fila])

        tabla = Table(filas_envueltas, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), _NEGRO),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, _FILA_ALT]),
            ('GRID', (0, 0), (-1, -1), 0.4, _BORDE),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elementos.append(tabla)
    else:
        elementos.append(Paragraph(
            'No hay datos para este reporte con los filtros seleccionados.',
            ParagraphStyle('vacio', fontSize=10, textColor=_GRIS),
        ))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()
