from datetime import date, timedelta

from flask import jsonify

from app.extensions import db
from app.models import Aplicacion, Equipo, EquipoAppPolitica, UsoAplicacion
from app.routes._api_helpers import require_admin
from app.routes.api_equipos._core import _esta_en_linea

from ..api_auth import jwt_required
from ._core import bp


@bp.route('/resumen', methods=['GET'])
@jwt_required
def resumen():
    err = require_admin()
    if err:
        return err

    equipos = Equipo.query.filter_by(activo=True).all()
    en_linea = sum(1 for e in equipos if _esta_en_linea(e))
    total = len(equipos)

    apps_bloqueadas = (
        db.session.query(EquipoAppPolitica)
        .join(Equipo, EquipoAppPolitica.equipo_id == Equipo.id)
        .filter(Equipo.activo.is_(True), EquipoAppPolitica.estado == 'bloqueada')
        .count()
    )

    hace_7dias = date.today() - timedelta(days=6)
    filas_uso = (
        db.session.query(UsoAplicacion, Aplicacion.nombre, Aplicacion.ejecutable)
        .join(Aplicacion, UsoAplicacion.aplicacion_id == Aplicacion.id)
        .filter(UsoAplicacion.fecha >= hace_7dias)
        .all()
    )
    acumulado = {}
    for uso, nombre, ejecutable in filas_uso:
        clave = uso.aplicacion_id
        item = acumulado.setdefault(clave, {'nombre': nombre, 'ejecutable': ejecutable, 'segundos': 0})
        item['segundos'] += uso.segundos or 0
    top_aplicaciones = sorted(acumulado.values(), key=lambda x: x['segundos'], reverse=True)[:5]

    return jsonify({
        'equipos_registrados': total,
        'en_linea': en_linea,
        'fuera_linea': total - en_linea,
        'apps_bloqueadas': apps_bloqueadas,
        'top_aplicaciones': top_aplicaciones,
    })
