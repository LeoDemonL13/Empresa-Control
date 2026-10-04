import os
import sys

from cryptography.fernet import Fernet

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('SECRET_KEY', 'clave-de-pruebas-solo-para-tests-0123456789')
os.environ.setdefault('TOTP_ENCRYPTION_KEY', Fernet.generate_key().decode())
os.environ['SOCKETIO_ASYNC_MODE'] = 'threading'
os.environ.setdefault('REDIS_URL', 'redis://127.0.0.1:6399/0')
os.environ['SOCKETIO_MESSAGE_QUEUE'] = 'false'

import pytest

from app import create_app
from app.extensions import db, get_redis


@pytest.fixture()
def app(tmp_path):
    os.environ['DATABASE_URL'] = f"sqlite:///{tmp_path / 'test.db'}"
    application = create_app()
    application.config['TESTING'] = True
    with application.app_context():
        db.create_all()
        r = get_redis()
        if r is not None:
            r.flushdb()
        yield application
        r = get_redis()
        if r is not None:
            r.flushdb()
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def super_admin(app):
    from werkzeug.security import generate_password_hash

    from app.constants import ROLE_SUPER_ADMIN
    from app.models import User

    u = User(
        username='root@nexus.mx',
        password_hash=generate_password_hash('Cl4ve-Segura-Prueba!'),
        role=ROLE_SUPER_ADMIN,
        full_name='Root',
    )
    db.session.add(u)
    db.session.commit()
    return u


@pytest.fixture()
def admin(app):
    from werkzeug.security import generate_password_hash

    from app.constants import ROLE_ADMIN
    from app.models import User

    u = User(
        username='ana@nexus.mx',
        password_hash=generate_password_hash('Cl4ve-Segura-Prueba!'),
        role=ROLE_ADMIN,
        full_name='Ana',
    )
    db.session.add(u)
    db.session.commit()
    return u


def login(client, username, password='Cl4ve-Segura-Prueba!'):
    return client.post('/api/auth/login', json={'username': username, 'password': password})


def auth_headers(token):
    return {'Authorization': f'Bearer {token}'}
