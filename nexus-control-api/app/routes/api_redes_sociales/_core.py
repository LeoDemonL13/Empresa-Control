from flask import Blueprint

bp = Blueprint('api_redes_sociales', __name__, url_prefix='/api/redes-sociales')

COOLDOWN_SINCRONIZACION_SEGUNDOS = 60
