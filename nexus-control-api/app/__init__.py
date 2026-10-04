import logging
import os
import time as _time
import traceback
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_compress import Compress
from flask_cors import CORS
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFError
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from app.extensions import csrf, db, limiter, migrate
from app.realtime import init_socketio, socketio

_MENSAJES_HTTP = {
    400: 'Solicitud inválida.',
    401: 'Autenticación requerida.',
    403: 'Acceso denegado.',
    404: 'Recurso no encontrado.',
    405: 'Método no permitido.',
    409: 'La operación entra en conflicto con el estado actual.',
    413: 'El contenido enviado es demasiado grande.',
    415: 'Tipo de contenido no soportado.',
    422: 'No se pudo procesar el contenido enviado.',
}


def create_app():
    load_dotenv()

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        static_folder=None,
        template_folder=os.path.join(BASE_DIR, 'templates'),
    )

    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        raise RuntimeError(
            "CRÍTICO: No se encontró SECRET_KEY en las variables de entorno. "
            "La aplicación no puede arrancar de forma segura."
        )

    app.config['SECRET_KEY'] = secret_key
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or secret_key
    app.config['BASE_DIR'] = BASE_DIR

    _db_uri = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = _db_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if not _db_uri.startswith('sqlite'):
        _engine_opts = {
            'pool_pre_ping': True,
            'pool_recycle': 1800,
            'pool_timeout': 30,
            'pool_size': int(os.environ.get('DB_POOL_SIZE', '10')),
            'max_overflow': int(os.environ.get('DB_MAX_OVERFLOW', '10')),
        }
        if _db_uri.startswith('postgresql'):
            _engine_opts['connect_args'] = {
                'options': '-c statement_timeout=30000 -c lock_timeout=5000'
            }
        app.config['SQLALCHEMY_ENGINE_OPTIONS'] = _engine_opts

    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
    app.config['COMPRESS_ALGORITHM'] = ['brotli', 'gzip', 'deflate']

    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=20)
    app.config['SESSION_COOKIE_SECURE'] = True

    is_prod = os.environ.get('FLASK_ENV', '').strip().lower() == 'production'

    app.config['RATELIMIT_DEFAULT'] = "2000 per day, 500 per hour"
    app.config['RATELIMIT_HEADERS_ENABLED'] = True

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    redis_url = os.environ.get('REDIS_URL')
    if redis_url and not redis_url.startswith('memory://'):
        import redis

        max_retries = 30
        retries = 0
        logging.info("Intentando conectar a Redis en: %s", redis_url)
        while retries < max_retries:
            try:
                client = redis.from_url(redis_url)
                if client.ping():
                    logging.info("Conexión a Redis exitosa.")
                    break
            except redis.RedisError as e:
                retries += 1
                logging.warning(
                    "Esperando a que Redis inicie... (Intento %s/%s). Error: %s",
                    retries, max_retries, e,
                )
                _time.sleep(2)
        if retries == max_retries:
            raise RuntimeError("CRÍTICO: No se pudo conectar a Redis. La aplicación no puede arrancar.")

    app.config['RATELIMIT_STORAGE_URI'] = redis_url or 'memory://'

    db.init_app(app)
    limiter.init_app(app)
    csrf.init_app(app)
    migrate.init_app(app, db)
    Compress(app)

    cors_origins = [
        o.strip()
        for o in os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://127.0.0.1:5173').split(',')
        if o.strip()
    ]
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
        methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization', 'X-Requested-With', 'X-CSRF-Token'],
        expose_headers=[
            'Content-Disposition',
            'X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset',
            'Retry-After',
        ],
        max_age=600,
    )

    csp = {
        'default-src': '\'none\'',
        'frame-ancestors': '\'none\'',
        'base-uri': '\'none\'',
        'form-action': '\'none\'',
    }
    _hsts_preload = os.environ.get('HSTS_PRELOAD', 'false').lower() == 'true'
    Talisman(
        app,
        content_security_policy=csp,
        force_https=False,
        frame_options='DENY',
        strict_transport_security=is_prod,
        strict_transport_security_max_age=31536000,
        strict_transport_security_include_subdomains=True,
        strict_transport_security_preload=_hsts_preload,
    )

    from app.routes import MODULOS_API

    for mod in MODULOS_API:
        csrf.exempt(mod.bp)
        app.register_blueprint(mod.bp)

    @app.errorhandler(CSRFError)
    def handle_csrf(e):
        return jsonify({'error': 'Tu formulario expiró, inténtalo de nuevo.'}), 419

    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({'error': "Has excedido el número de intentos permitidos."}), 429

    @app.errorhandler(Exception)
    def handle_exception(e):
        if isinstance(e, HTTPException) and e.code != 500:
            mensaje = _MENSAJES_HTTP.get(e.code) or e.description or 'Error en la solicitud.'
            respuesta = jsonify({'error': mensaje})
            respuesta.status_code = e.code
            for nombre, valor in (e.get_headers() or []):
                if nombre.lower() in ('allow', 'retry-after', 'www-authenticate'):
                    respuesta.headers[nombre] = valor
            return respuesta
        try:
            if is_prod:
                app.logger.error(
                    "Internal Server Error [%s] %s %s",
                    type(e).__name__, request.method, request.path,
                )
            else:
                app.logger.error("Internal Server Error: %s\n%s", str(e), traceback.format_exc())
            try:
                db.session.rollback()
            except Exception:
                pass
            return jsonify({'error': "Ocurrió un error interno en el servidor."}), 500
        except Exception as handler_error:
            app.logger.error("Critical error in 500 handler: %s", str(handler_error)[:200])
            return "Internal Server Error", 500

    @app.route('/')
    @app.route('/health')
    @limiter.exempt
    def _health():
        return jsonify({'status': 'ok'})

    @app.before_request
    def _start_timer():
        request._start_time = _time.time()

    @app.after_request
    def _security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
        response.headers.setdefault('Permissions-Policy', 'camera=(), microphone=(), geolocation=()')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Cross-Origin-Opener-Policy', 'same-origin')
        response.headers.setdefault('Cross-Origin-Resource-Policy', 'same-origin')
        path = request.path or ''
        if path.startswith('/api/') or path in ('/', '/health'):
            response.headers.setdefault('Cache-Control', 'no-store, no-cache, must-revalidate')
        ctype = response.mimetype or ''
        if ctype == 'application/pdf' or 'spreadsheetml' in ctype or ctype == 'application/vnd.ms-excel':
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
        return response

    @app.after_request
    def _log_request(response):
        elapsed_ms = (_time.time() - getattr(request, '_start_time', _time.time())) * 1000
        if elapsed_ms > 500 or response.status_code >= 400:
            app.logger.log(
                logging.WARNING if response.status_code >= 400 else logging.INFO,
                "[PERF] %s %s -> %s (%.0fms)",
                request.method, request.path, response.status_code, elapsed_ms,
            )
        return response

    os.makedirs(os.path.join(BASE_DIR, 'data'), exist_ok=True)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=2, x_proto=1, x_host=1, x_prefix=1)

    init_socketio(app)
    return app


__all__ = ['create_app', 'socketio']
