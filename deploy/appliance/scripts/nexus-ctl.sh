#!/usr/bin/env bash
set -euo pipefail

. /opt/nexus/scripts/lib.sh

uso() {
    echo "Uso: nexus-ctl {estado|logs [servicio]|actualizar|respaldar|respaldos|restaurar ARCHIVO|aplicar|reiniciar}"
}

comando=${1:-}
shift || true

case "$comando" in
    estado)
        dc ps
        echo
        if salud_ok; then echo "App: OK"; else echo "App: SIN RESPUESTA"; fi
        if tunel_ok; then echo "Tunel: OK"; else echo "Tunel: SIN CONEXION"; fi
        echo "Revision de base: $(revision_actual)"
        echo "Imagen api: $(docker image inspect --format '{{.Id}}' "$(imagen_api):stable" 2>/dev/null | cut -c1-19)"
        df -h / | tail -n 1
        ;;
    logs)
        dc logs --tail 200 -f "${1:-api}"
        ;;
    actualizar)
        /opt/nexus/scripts/nexus-update.sh
        ;;
    respaldar)
        /opt/nexus/scripts/nexus-backup.sh
        ;;
    respaldos)
        ls -lh "$BACKUP_DIR"
        ;;
    restaurar)
        archivo=${1:-}
        [ -f "$archivo" ] || { echo "Indica un archivo .sql.gz existente (ver: nexus-ctl respaldos)"; exit 1; }
        read -r -p "Esto reemplaza TODA la base actual por $archivo. Escribe RESTAURAR para continuar: " confirmacion
        [ "$confirmacion" = "RESTAURAR" ] || { echo "Cancelado."; exit 1; }
        restaurar_base "$archivo"
        dc up -d api web
        if esperar_salud 240; then
            echo "Restaurado y saludable."
        else
            echo "Restaurado pero la app no responde; revisa: nexus-ctl logs api"
            exit 1
        fi
        ;;
    aplicar)
        dc up -d --force-recreate api
        ;;
    reiniciar)
        dc restart
        ;;
    *)
        uso
        exit 1
        ;;
esac
