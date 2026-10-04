from datetime import date, datetime, timedelta

from app.models import AuditLog, Aplicacion, Equipo, UsoAplicacion
from app.routes.api_equipos._core import _esta_en_linea


def _formatear_duracion(segundos: int) -> str:
    segundos = segundos or 0
    horas, resto = divmod(segundos, 3600)
    minutos, segs = divmod(resto, 60)
    if horas:
        return f'{horas} h {minutos} min'
    if minutos:
        return f'{minutos} min {segs} s'
    return f'{segs} s'


_ETIQUETA_TIPO_EQUIPO = {'pc': 'PC', 'android': 'Android'}


def datos_general():
    columnas = [
        'Equipo', 'Tipo', 'Categoría', 'Usuario asignado', 'IP', 'MAC', 'Hostname',
        'Sistema operativo', 'Agente', 'Estado', 'Alta',
    ]
    equipos = Equipo.query.filter_by(activo=True).order_by(Equipo.nombre.asc()).all()
    filas = []
    for e in equipos:
        filas.append([
            e.nombre,
            _ETIQUETA_TIPO_EQUIPO.get(e.tipo, e.tipo),
            e.categoria.nombre if e.categoria else 'Sin categoría',
            e.usuario_asignado or '—',
            e.ip or '—',
            e.mac or '—',
            e.hostname or '—',
            e.sistema_operativo or '—',
            f'v{e.agente_version}' if e.agente_version else 'No enrolado',
            'En línea' if _esta_en_linea(e) else 'Fuera de línea',
            e.created_at.strftime('%d/%m/%Y') if e.created_at else '—',
        ])
    return columnas, filas


def datos_uso(desde: date, hasta: date, equipo_id: int | None = None, categoria_id: int | None = None):
    columnas = ['Equipo', 'Aplicación', 'Ejecutable', 'Tiempo de uso', 'Sesiones', 'Fecha']

    query = (
        UsoAplicacion.query
        .join(Equipo, UsoAplicacion.equipo_id == Equipo.id)
        .join(Aplicacion, UsoAplicacion.aplicacion_id == Aplicacion.id)
        .filter(UsoAplicacion.fecha >= desde, UsoAplicacion.fecha <= hasta, Equipo.activo.is_(True))
    )
    if equipo_id:
        query = query.filter(Equipo.id == equipo_id)
    if categoria_id:
        query = query.filter(Equipo.categoria_id == categoria_id)

    filas_raw = (
        query.add_columns(Equipo.nombre, Aplicacion.nombre, Aplicacion.ejecutable)
        .order_by(UsoAplicacion.fecha.desc())
        .all()
    )
    filas = []
    for uso, equipo_nombre, app_nombre, ejecutable in filas_raw:
        filas.append([
            equipo_nombre, app_nombre, ejecutable,
            _formatear_duracion(uso.segundos),
            uso.sesiones or 0,
            uso.fecha.strftime('%d/%m/%Y') if uso.fecha else '—',
        ])
    return columnas, filas


def datos_auditoria(
    desde: date, hasta: date,
    usuario: str | None = None, entidad: str | None = None, origen: str | None = None,
):
    columnas = ['Fecha', 'Usuario', 'Acción', 'Entidad', 'Origen', 'IP']

    inicio = datetime.combine(desde, datetime.min.time())
    fin = datetime.combine(hasta, datetime.min.time()) + timedelta(days=1)
    query = AuditLog.query.filter(AuditLog.created_at >= inicio, AuditLog.created_at < fin)
    if usuario:
        query = query.filter(AuditLog.user.ilike(f'%{usuario}%'))
    if entidad:
        query = query.filter(AuditLog.entidad == entidad)
    if origen:
        query = query.filter(AuditLog.origen == origen)

    filas = []
    for log in query.order_by(AuditLog.created_at.desc()).all():
        filas.append([
            log.created_at.strftime('%d/%m/%Y %H:%M') if log.created_at else '—',
            log.user or 'Sistema',
            log.action,
            log.entidad or '—',
            log.origen or '—',
            log.ip or '—',
        ])
    return columnas, filas
