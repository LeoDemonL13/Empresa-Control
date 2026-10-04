from flask import g, jsonify

from app.extensions import limiter
from app.models import Aplicacion, EquipoAppPolitica

from ._core import agente_requerido, bp


@bp.route('/politicas', methods=['GET'])
@agente_requerido
@limiter.limit('30 per minute')
def obtener_politicas():
    equipo = g._equipo

    politicas = (
        EquipoAppPolitica.query
        .filter_by(equipo_id=equipo.id)
        .join(Aplicacion)
        .all()
    )

    return jsonify({
        'politica_version': equipo.politica_version,
        'politicas': [
            {
                'ejecutable': p.aplicacion.ejecutable,
                'estado': p.estado,
                'tipo_uso': p.tipo_uso,
                'limite_minutos': p.limite_minutos,
                'periodo': p.periodo,
            }
            for p in politicas
        ],
    })
