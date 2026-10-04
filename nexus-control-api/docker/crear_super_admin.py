import os
import sys

sys.path.insert(0, os.getcwd())

from werkzeug.security import check_password_hash, generate_password_hash

from app import create_app
from app.constants import ROLE_SUPER_ADMIN
from app.extensions import db
from app.models import User
from app.utils.security import PASSWORD_MIN_LEN, is_strong_password


def main() -> int:
    username = os.environ.get('SUPERADMIN_USERNAME', '').strip()
    password = os.environ.get('SUPERADMIN_PASSWORD', '')
    full_name = os.environ.get('SUPERADMIN_FULL_NAME', '').strip() or None
    forzar = os.environ.get('SUPERADMIN_FORZAR_PASSWORD', 'false').strip().lower() == 'true'

    if not username or not password:
        print(
            '[super_admin] CRÍTICO: define SUPERADMIN_USERNAME y SUPERADMIN_PASSWORD en el .env.',
            file=sys.stderr,
        )
        return 1

    app = create_app()
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        creado = user is None

        if creado:
            if not is_strong_password(password):
                print(
                    f'[super_admin] CRÍTICO: la contraseña debe tener al menos {PASSWORD_MIN_LEN} '
                    'caracteres, con mayúscula, minúscula, número y símbolo.',
                    file=sys.stderr,
                )
                return 1
            user = User(username=username, password_hash=generate_password_hash(password))
            db.session.add(user)

        cambios = creado

        if not creado and forzar:
            if not is_strong_password(password):
                print('[super_admin] CRÍTICO: la contraseña no cumple la política de seguridad.', file=sys.stderr)
                return 1
            if not check_password_hash(user.password_hash, password):
                user.password_hash = generate_password_hash(password)
                user.password_version = (user.password_version or 1) + 1
                user.totp_secret = None
                cambios = True

        if user.role != ROLE_SUPER_ADMIN:
            user.role = ROLE_SUPER_ADMIN
            user.password_version = (user.password_version or 1) + (0 if creado else 1)
            cambios = True

        if not user.activo:
            user.activo = True
            cambios = True

        if full_name and user.full_name != full_name:
            user.full_name = full_name
            cambios = True

        if not user.position:
            user.position = 'Súper administrador'
            cambios = True

        if not user.password_version:
            user.password_version = 1

        db.session.commit()

        verificado = User.query.filter_by(username=username).first()
        if verificado is None or verificado.role != ROLE_SUPER_ADMIN or not verificado.activo:
            print('[super_admin] CRÍTICO: no se pudo garantizar el usuario súper administrador.', file=sys.stderr)
            return 1

        estado = 'creado' if creado else ('actualizado' if cambios else 'sin cambios')
        print(f'[super_admin] {verificado.username} | {verificado.role} | {estado}')
        return 0


if __name__ == '__main__':
    sys.exit(main())
