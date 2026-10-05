import os

import pytest

from app import create_app
from app.extensions import db
from app.models import AuditLog, User
from app.utils import log_action


def test_health_responde_ok(client):
    r = client.get('/health')
    assert r.status_code == 200
    assert r.get_json() == {'status': 'ok'}


def test_cabeceras_de_seguridad(client):
    r = client.get('/health')
    assert r.headers['X-Content-Type-Options'] == 'nosniff'
    assert r.headers['X-Frame-Options'] == 'DENY'
    assert r.headers['Cross-Origin-Opener-Policy'] == 'same-origin'
    assert 'no-store' in r.headers['Cache-Control']
    assert "default-src 'none'" in r.headers['Content-Security-Policy']


def test_ruta_inexistente_devuelve_json_estandar(client):
    r = client.get('/api/no-existe')
    assert r.status_code == 404
    assert r.get_json() == {'error': 'Recurso no encontrado.'}


def test_metodo_no_permitido_devuelve_json_estandar(client):
    r = client.post('/health')
    assert r.status_code == 405
    assert r.get_json() == {'error': 'Método no permitido.'}


def test_error_interno_no_filtra_detalles(app):
    @app.route('/api/falla')
    def _falla():
        raise ValueError('secreto interno')

    app.config['PROPAGATE_EXCEPTIONS'] = False
    app.config['TESTING'] = False
    r = app.test_client().get('/api/falla')
    assert r.status_code == 500
    assert r.get_json() == {'error': 'Ocurrió un error interno en el servidor.'}


def test_arranque_sin_secret_key_falla(monkeypatch):
    monkeypatch.delenv('SECRET_KEY', raising=False)
    monkeypatch.setattr('app.load_dotenv', lambda: None)
    with pytest.raises(RuntimeError, match='SECRET_KEY'):
        create_app()


def test_cors_solo_permite_origenes_configurados(client):
    permitido = client.options(
        '/api/lo-que-sea',
        headers={'Origin': 'http://localhost:5173', 'Access-Control-Request-Method': 'GET'},
    )
    assert permitido.headers.get('Access-Control-Allow-Origin') == 'http://localhost:5173'
    ajeno = client.options(
        '/api/lo-que-sea',
        headers={'Origin': 'http://sitio-ajeno.example', 'Access-Control-Request-Method': 'GET'},
    )
    assert 'Access-Control-Allow-Origin' not in ajeno.headers


def test_log_action_registra_bitacora_con_detalle(app):
    with app.test_request_context('/'):
        log_action('equipo.crear', entidad='equipo', entidad_id=7, detalle={'antes': None, 'despues': {'nombre': 'PC-01'}})
    registro = AuditLog.query.one()
    assert registro.user == 'anon'
    assert registro.action == 'equipo.crear'
    assert registro.entidad == 'equipo'
    assert registro.entidad_id == 7
    assert registro.detalle['despues']['nombre'] == 'PC-01'
    assert registro.origen == 'panel'


def test_log_action_neutraliza_saltos_de_linea(app):
    with app.test_request_context('/'):
        log_action('login\nfalso: exito')
    assert '\n' not in AuditLog.query.one().action


def test_totp_secret_se_guarda_cifrado(app):
    u = User(username='a@b.mx', password_hash='x')
    u.totp_secret = 'JBSWY3DPEHPK3PXP'
    db.session.add(u)
    db.session.commit()
    crudo = db.session.execute(db.text('SELECT totp_secret FROM users')).scalar()
    assert crudo != 'JBSWY3DPEHPK3PXP'
    db.session.expire_all()
    assert User.query.one().totp_secret == 'JBSWY3DPEHPK3PXP'


def _ip_vista_por_la_app(monkeypatch, saltos):
    from app import create_app

    if saltos is None:
        monkeypatch.delenv('PROXY_FOR_HOPS', raising=False)
    else:
        monkeypatch.setenv('PROXY_FOR_HOPS', saltos)
    aplicacion = create_app()

    @aplicacion.route('/_ip_prueba')
    def _ip_prueba():
        from flask import request
        return request.remote_addr or ''

    r = aplicacion.test_client().get(
        '/_ip_prueba',
        headers={'X-Forwarded-For': '203.0.113.7'},
        environ_base={'REMOTE_ADDR': '172.18.0.5'},
    )
    return r.get_data(as_text=True)


def test_proxyfix_por_defecto_ignora_un_solo_salto(monkeypatch, tmp_path):
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path / 'a.db'}")
    assert _ip_vista_por_la_app(monkeypatch, None) == '172.18.0.5'


def test_proxyfix_con_un_salto_toma_la_ip_del_cliente(monkeypatch, tmp_path):
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path / 'b.db'}")
    assert _ip_vista_por_la_app(monkeypatch, '1') == '203.0.113.7'


def test_proxyfix_valor_invalido_cae_al_defecto(monkeypatch, tmp_path):
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path / 'c.db'}")
    assert _ip_vista_por_la_app(monkeypatch, 'abc') == '172.18.0.5'
