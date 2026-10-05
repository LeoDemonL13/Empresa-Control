NEXUS_DIR=/opt/nexus
ENV_FILE=/etc/nexus/.env
export STATE_DIR=/var/lib/nexus
export BACKUP_DIR=/var/backups/nexus
COMPOSE_FILE=$NEXUS_DIR/docker-compose.appliance.yml

dc() {
    docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE" "$@"
}

leer_env() {
    grep -E "^$1=" "$ENV_FILE" | tail -n 1 | cut -d= -f2- || true
}

registrar() {
    logger -t nexus "$*"
    printf '%s %s\n' "$(date -Is)" "$*"
}

alertar() {
    local url
    url=$(leer_env ALERT_WEBHOOK_URL)
    [ -n "$url" ] || return 0
    curl -fsS -m 10 -H 'Content-Type: application/json' \
        -d "{\"text\":\"[$(hostname)] $1\"}" "$url" >/dev/null 2>&1 || true
}

salud_ok() {
    dc exec -T web wget -qO- -T 4 http://127.0.0.1/health 2>/dev/null | grep -q '"ok"'
}

tunel_ok() {
    dc exec -T web wget -qO /dev/null -T 4 http://tunnel:2000/ready 2>/dev/null
}

esperar_salud() {
    local limite=$1 transcurrido=0
    while [ "$transcurrido" -lt "$limite" ]; do
        if salud_ok; then
            return 0
        fi
        sleep 5
        transcurrido=$((transcurrido + 5))
    done
    return 1
}

revision_actual() {
    local usuario base
    usuario=$(leer_env POSTGRES_USER)
    base=$(leer_env POSTGRES_DB)
    dc exec -T db psql -U "$usuario" -d "$base" -Atc 'select version_num from alembic_version' 2>/dev/null | tr -d '[:space:]' || true
}

respaldar_base() {
    local destino=$1 usuario base
    usuario=$(leer_env POSTGRES_USER)
    base=$(leer_env POSTGRES_DB)
    mkdir -p "$(dirname "$destino")"
    if ! dc exec -T db pg_dump -U "$usuario" -d "$base" --no-owner | gzip >"$destino.tmp"; then
        rm -f "$destino.tmp"
        return 1
    fi
    if ! gzip -t "$destino.tmp" || [ "$(stat -c %s "$destino.tmp")" -lt 200 ]; then
        rm -f "$destino.tmp"
        return 1
    fi
    mv "$destino.tmp" "$destino"
    chmod 600 "$destino"
}

restaurar_base() {
    local origen=$1 usuario base
    usuario=$(leer_env POSTGRES_USER)
    base=$(leer_env POSTGRES_DB)
    gzip -t "$origen"
    dc stop api web
    dc exec -T db psql -U "$usuario" -d postgres -v ON_ERROR_STOP=1 \
        -c "DROP DATABASE IF EXISTS \"$base\" WITH (FORCE)" \
        -c "CREATE DATABASE \"$base\" OWNER \"$usuario\""
    gunzip -c "$origen" | dc exec -T db psql -U "$usuario" -d "$base" -v ON_ERROR_STOP=1 -q >/dev/null
}

imagen_api() {
    printf 'ghcr.io/%s/nexus-api' "$(leer_env GHCR_OWNER)"
}

imagen_web() {
    printf 'ghcr.io/%s/nexus-web' "$(leer_env GHCR_OWNER)"
}

id_imagen() {
    docker image inspect --format '{{.Id}}' "$1" 2>/dev/null || true
}

rotar() {
    find "$BACKUP_DIR" -maxdepth 1 -type f -name "$1" -printf '%T@ %p\n' \
        | sort -rn | tail -n +"$(($2 + 1))" | cut -d' ' -f2- | xargs -r rm --
}
