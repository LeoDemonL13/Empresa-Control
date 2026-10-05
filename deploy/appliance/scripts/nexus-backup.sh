#!/usr/bin/env bash
set -euo pipefail

. /opt/nexus/scripts/lib.sh

exec 8>/var/lock/nexus-backup.lock
flock -n 8 || exit 0

mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"

destino="$BACKUP_DIR/nexus-$(date +%Y%m%d-%H%M%S).sql.gz"

if ! respaldar_base "$destino"; then
    registrar "respaldo: fallo"
    alertar "El respaldo diario de la base de datos fallo."
    exit 1
fi

cp /etc/nexus/.env "$BACKUP_DIR/env-$(date +%Y%m%d).bak"
chmod 600 "$BACKUP_DIR"/env-*.bak
rotar 'env-*.bak' 7
rotar 'nexus-*.sql.gz' 14

registrar "respaldo: ok ($destino)"
