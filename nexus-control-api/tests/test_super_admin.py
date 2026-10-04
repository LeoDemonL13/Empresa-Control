import importlib.util
import os

import pytest
from werkzeug.security import check_password_hash

from app.extensions import db
from app.models import User

RUTA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'docker', 'crear_super_admin.py')
PASSWORD_VALIDA = 'Cl4ve-Segura-Prueba!'


def _ejecutar(monkeypatch, **entorno):
    for nombre in ('SUPERADMIN_USERNAME', 'SUPERADMIN_PASSWORD', 'SUPERADMIN_FULL_NAME', 'SUPERADMIN_FORZAR_PASSWORD'):
        monkeypatch.delenv(nombre, raising=False)
    for nombre, valor in entorno.items():
        monkeypatch.setenv(nombre, valor)
    spec = importlib.util.spec_from_file_location('crear_super_admin', RUTA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo.main()


@pytest.fixture()
def contexto(app, monkeypatch):
    monkeypatch.setattr('app.create_app', lambda: app)
    return app


def test_sin_credenciales_no_crea_nada(contexto, monkeypatch, capsys):
    assert _ejecutar(monkeypatch) == 1
    assert User.query.count() == 0
    assert 'SUPERADMIN_USERNAME' in capsys.readouterr().err


def test_rechaza_contrasena_debil(contexto, monkeypatch):
    codigo = _ejecutar(monkeypatch, SUPERADMIN_USERNAME='root@nexus.mx', SUPERADMIN_PASSWORD='corta')
    assert codigo == 1
    assert User.query.count() == 0


def test_crea_super_admin(contexto, monkeypatch):
    codigo = _ejecutar(
        monkeypatch,
        SUPERADMIN_USERNAME='root@nexus.mx',
        SUPERADMIN_PASSWORD=PASSWORD_VALIDA,
        SUPERADMIN_FULL_NAME='Administrador General',
    )
    assert codigo == 0
    u = User.query.one()
    assert u.role == 'super_admin'
    assert u.activo is True
    assert u.full_name == 'Administrador General'
    assert u.password_version == 1
    assert check_password_hash(u.password_hash, PASSWORD_VALIDA)
    assert u.password_hash != PASSWORD_VALIDA


def test_es_idempotente_y_no_pisa_la_contrasena(contexto, monkeypatch):
    _ejecutar(monkeypatch, SUPERADMIN_USERNAME='root@nexus.mx', SUPERADMIN_PASSWORD=PASSWORD_VALIDA)
    u = User.query.one()
    u.password_hash = 'hash-cambiado-desde-el-panel'
    db.session.commit()

    _ejecutar(monkeypatch, SUPERADMIN_USERNAME='root@nexus.mx', SUPERADMIN_PASSWORD=PASSWORD_VALIDA)
    assert User.query.count() == 1
    assert User.query.one().password_hash == 'hash-cambiado-desde-el-panel'


def test_forzar_password_invalida_sesiones(contexto, monkeypatch):
    _ejecutar(monkeypatch, SUPERADMIN_USERNAME='root@nexus.mx', SUPERADMIN_PASSWORD=PASSWORD_VALIDA)
    nueva = 'Otra-Clave-Segura-77!'
    _ejecutar(
        monkeypatch,
        SUPERADMIN_USERNAME='root@nexus.mx',
        SUPERADMIN_PASSWORD=nueva,
        SUPERADMIN_FORZAR_PASSWORD='true',
    )
    u = User.query.one()
    assert check_password_hash(u.password_hash, nueva)
    assert u.password_version == 2


def test_promueve_y_reactiva_un_usuario_existente(contexto, monkeypatch):
    db.session.add(User(username='root@nexus.mx', password_hash='x', role='admin', activo=False))
    db.session.commit()
    assert _ejecutar(monkeypatch, SUPERADMIN_USERNAME='root@nexus.mx', SUPERADMIN_PASSWORD=PASSWORD_VALIDA) == 0
    u = User.query.one()
    assert u.role == 'super_admin'
    assert u.activo is True


def test_no_toca_a_otros_administradores(contexto, monkeypatch):
    db.session.add(User(username='otro@nexus.mx', password_hash='x', role='admin'))
    db.session.commit()
    _ejecutar(monkeypatch, SUPERADMIN_USERNAME='root@nexus.mx', SUPERADMIN_PASSWORD=PASSWORD_VALIDA)
    assert User.query.filter_by(username='otro@nexus.mx').one().role == 'admin'
