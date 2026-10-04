from flask import Blueprint, Response

from app.reportes import generar_csv, generar_pdf, generar_xlsx

bp = Blueprint('api_reportes', __name__, url_prefix='/api/reportes')

FORMATOS_VALIDOS = ('pdf', 'csv', 'xlsx')

_MIME = {
    'pdf': 'application/pdf',
    'csv': 'text/csv',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}


def _validar_formato(valor):
    formato = (valor or 'pdf').strip().lower()
    return formato if formato in FORMATOS_VALIDOS else None


def _construir_respuesta(formato, titulo, subtitulo, columnas, filas, generado_por, nombre_archivo):
    if formato == 'pdf':
        contenido = generar_pdf(titulo, subtitulo, columnas, filas, generado_por)
    elif formato == 'xlsx':
        contenido = generar_xlsx(titulo, columnas, filas)
    else:
        contenido = generar_csv(columnas, filas)

    respuesta = Response(contenido, mimetype=_MIME[formato])
    respuesta.headers['Content-Disposition'] = f'attachment; filename="{nombre_archivo}.{formato}"'
    respuesta.headers['Content-Length'] = str(len(contenido))
    return respuesta
