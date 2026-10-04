#!/bin/sh
set -eu

case "${1:-}" in
    gunicorn) es_servidor=si ;;
    flask)    es_servidor=no ;;
    *)
        echo "[entrypoint] Comando suelto ($1): sin espera de base ni migraciones."
        exec "$@"
        ;;
esac

if [ -z "${SECRET_KEY:-}" ]; then
    echo "[entrypoint] CRÍTICO: falta SECRET_KEY. Revisa el env_file del compose." >&2
    exit 1
fi

if [ -z "${TOTP_ENCRYPTION_KEY:-}" ]; then
    echo "[entrypoint] CRÍTICO: falta TOTP_ENCRYPTION_KEY. Revisa el env_file del compose." >&2
    exit 1
fi

python /usr/local/bin/espera_db.py

if [ "$es_servidor" = "no" ]; then
    echo "[entrypoint] Ejecutando: $*"
    exec "$@"
fi

if [ "${APLICAR_MIGRACIONES:-true}" = "true" ]; then
    python /usr/local/bin/bootstrap_esquema.py
    flask db upgrade
    echo "[entrypoint] Revisión aplicada: $(python /usr/local/bin/revision_actual.py 2>&1 | tail -1)"
else
    echo "[entrypoint] APLICAR_MIGRACIONES=false. Revisión en la base:" \
         "$(python /usr/local/bin/revision_actual.py 2>&1 | tail -1)"
fi

if [ "${CREAR_SUPER_ADMIN:-false}" = "true" ]; then
    python docker/crear_super_admin.py
fi

echo "[entrypoint] Arrancando: $*"
exec "$@"
