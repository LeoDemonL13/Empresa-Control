#!/usr/bin/env bash
set -euo pipefail

. /opt/nexus/scripts/lib.sh

exec 9>/var/lock/nexus-update.lock
flock -n 9 || exit 0

trap 'registrar "actualizacion: error inesperado"; alertar "Error inesperado durante la actualizacion. Revisar por SSH: journalctl -t nexus"' ERR

mkdir -p "$STATE_DIR" "$BACKUP_DIR"
touch "$STATE_DIR/ids_malos"

api=$(imagen_api):stable
web=$(imagen_web):stable
api_previa=$(imagen_api):previous
web_previa=$(imagen_web):previous

id_api_antes=$(id_imagen "$api")
id_web_antes=$(id_imagen "$web")

if ! dc pull api web >/dev/null 2>&1; then
    registrar "actualizacion: no se pudo consultar el registro, se reintentara luego"
    exit 0
fi

id_api_nueva=$(id_imagen "$api")
id_web_nueva=$(id_imagen "$web")

if [ "$id_api_antes" = "$id_api_nueva" ] && [ "$id_web_antes" = "$id_web_nueva" ]; then
    exit 0
fi

if grep -qxF "$id_api_nueva" "$STATE_DIR/ids_malos" || grep -qxF "$id_web_nueva" "$STATE_DIR/ids_malos"; then
    if [ -n "$id_api_antes" ]; then
        docker tag "$api_previa" "$api"
    fi
    if [ -n "$id_web_antes" ]; then
        docker tag "$web_previa" "$web"
    fi
    exit 0
fi

registrar "actualizacion: version nueva detectada, iniciando"

if [ -n "$id_api_antes" ]; then
    docker tag "$id_api_antes" "$api_previa"
fi
if [ -n "$id_web_antes" ]; then
    docker tag "$id_web_antes" "$web_previa"
fi

revision_antes=$(revision_actual)
respaldo="$BACKUP_DIR/pre-actualizacion-$(date +%Y%m%d-%H%M%S).sql.gz"

if ! respaldar_base "$respaldo"; then
    registrar "actualizacion: abortada, no se pudo respaldar la base"
    alertar "Actualizacion abortada: fallo el respaldo previo. El sistema sigue en la version anterior."
    if [ -n "$id_api_antes" ]; then
        docker tag "$api_previa" "$api"
    fi
    if [ -n "$id_web_antes" ]; then
        docker tag "$web_previa" "$web"
    fi
    exit 1
fi

dc up -d --remove-orphans api web

if esperar_salud 240; then
    sleep 20
    if salud_ok; then
        registrar "actualizacion: completada y saludable"
        docker image prune -f >/dev/null 2>&1 || true
        rotar 'pre-actualizacion-*.sql.gz' 5
        alertar "Actualizacion aplicada correctamente."
        exit 0
    fi
fi

registrar "actualizacion: la version nueva no quedo saludable, revirtiendo"
dc logs --tail 80 api >"$STATE_DIR/ultimo_fallo_api.log" 2>&1 || true
printf '%s\n%s\n' "$id_api_nueva" "$id_web_nueva" >>"$STATE_DIR/ids_malos"

if [ -n "$id_api_antes" ]; then
    docker tag "$api_previa" "$api"
fi
if [ -n "$id_web_antes" ]; then
    docker tag "$web_previa" "$web"
fi

revision_despues=$(revision_actual)
if [ "$revision_antes" != "$revision_despues" ]; then
    registrar "actualizacion: la migracion cambio la base ($revision_antes -> $revision_despues), restaurando respaldo"
    restaurar_base "$respaldo"
fi

dc up -d --force-recreate api web

if esperar_salud 240; then
    registrar "actualizacion: rollback exitoso"
    alertar "La actualizacion fallo y se revirtio automaticamente a la version anterior. El sistema funciona. Log en $STATE_DIR/ultimo_fallo_api.log"
    exit 1
fi

registrar "actualizacion: CRITICO, el rollback tampoco quedo saludable"
alertar "CRITICO: la actualizacion fallo y el rollback tampoco recupero el servicio. Requiere intervencion por SSH."
exit 2
