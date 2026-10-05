#!/usr/bin/env bash
set -euo pipefail

ORIGEN=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ENTRADA=${NEXUS_PROVISION_FILE:-/root/nexus-provision.env}
DESTINO=/opt/nexus
ENV_DEST=/etc/nexus/.env

if [ "$(id -u)" -ne 0 ]; then
    echo "Ejecuta este script como root (sudo)." >&2
    exit 1
fi

if [ ! -f "$ENTRADA" ]; then
    echo "Falta $ENTRADA con los datos de instalacion." >&2
    exit 1
fi

set -a
. "$ENTRADA"
set +a

: "${NEXUS_DOMAIN:?falta NEXUS_DOMAIN}"
: "${GHCR_OWNER:?falta GHCR_OWNER}"
: "${CLOUDFLARE_TUNNEL_TOKEN:?falta CLOUDFLARE_TUNNEL_TOKEN}"
: "${SUPERADMIN_USERNAME:?falta SUPERADMIN_USERNAME}"
GHCR_OWNER=$(printf '%s' "$GHCR_OWNER" | tr '[:upper:]' '[:lower:]')

fijar_var() {
    local clave=$1 valor=$2 tmp linea hallada=0
    tmp=$(mktemp)
    while IFS= read -r linea || [ -n "$linea" ]; do
        if [[ $linea == "$clave="* ]]; then
            printf '%s=%s\n' "$clave" "$valor" >>"$tmp"
            hallada=1
        else
            printf '%s\n' "$linea" >>"$tmp"
        fi
    done <"$ENV_DEST"
    if [ "$hallada" -eq 0 ]; then
        printf '%s=%s\n' "$clave" "$valor" >>"$tmp"
    fi
    cat "$tmp" >"$ENV_DEST"
    rm -f "$tmp"
}

leer_var() {
    grep -E "^$1=" "$ENV_DEST" | tail -n 1 | cut -d= -f2- || true
}

clave_base64() {
    openssl rand -base64 32 | tr '+/' '-_' | tr -d '\n'
}

echo "[1/9] Paquetes base y actualizaciones automaticas de seguridad"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y --no-install-recommends ca-certificates curl gnupg openssl ufw unattended-upgrades logrotate util-linux

cat >/etc/apt/apt.conf.d/52nexus-unattended <<'CFG'
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "04:30";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
CFG
cat >/etc/apt/apt.conf.d/20auto-upgrades <<'CFG'
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
CFG

echo "[2/9] Docker"
if ! command -v docker >/dev/null 2>&1; then
    curl -fsSL https://get.docker.com | sh
fi
mkdir -p /etc/docker
cat >/etc/docker/daemon.json <<'CFG'
{
  "log-driver": "json-file",
  "log-opts": { "max-size": "10m", "max-file": "5" },
  "live-restore": true
}
CFG
systemctl enable --now docker
systemctl restart docker

echo "[3/9] Red, energia y vigilancia del sistema"
install -m 600 "$ORIGEN/netplan/01-nexus.yaml" /etc/netplan/01-nexus.yaml
mkdir -p /etc/cloud/cloud.cfg.d
printf 'network: {config: disabled}\n' >/etc/cloud/cloud.cfg.d/99-nexus-sin-red.cfg
for f in /etc/netplan/*.yaml; do
    if [ "$f" != "/etc/netplan/01-nexus.yaml" ]; then
        mv "$f" "$f.desactivado"
    fi
done
netplan generate

systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target >/dev/null 2>&1 || true

mkdir -p /etc/systemd/system.conf.d /etc/systemd/journald.conf.d /etc/systemd/logind.conf.d
cat >/etc/systemd/system.conf.d/10-nexus-watchdog.conf <<'CFG'
[Manager]
RuntimeWatchdogSec=30
RebootWatchdogSec=10min
CFG
cat >/etc/systemd/journald.conf.d/10-nexus.conf <<'CFG'
[Journal]
Storage=persistent
SystemMaxUse=500M
CFG
cat >/etc/systemd/logind.conf.d/10-nexus.conf <<'CFG'
[Login]
HandlePowerKey=ignore
HandleSuspendKey=ignore
HandleLidSwitch=ignore
IdleAction=ignore
CFG
systemctl restart systemd-journald

echo "[4/9] Acceso remoto de administracion (Tailscale) y firewall"
if ! command -v tailscale >/dev/null 2>&1; then
    curl -fsSL https://tailscale.com/install.sh | sh
fi
if [ -n "${TAILSCALE_AUTHKEY:-}" ]; then
    tailscale up --authkey="$TAILSCALE_AUTHKEY" --ssh --hostname="${NEXUS_HOSTNAME:-nexus-minipc}" || true
fi

ufw --force reset >/dev/null
ufw default deny incoming
ufw default allow outgoing
ufw allow in on tailscale0
ufw allow from 10.0.0.0/8 to any port 22 proto tcp
ufw allow from 172.16.0.0/12 to any port 22 proto tcp
ufw allow from 192.168.0.0/16 to any port 22 proto tcp
ufw --force enable

echo "[5/9] Archivos de la aplicacion"
mkdir -p "$DESTINO/scripts" /etc/nexus /var/lib/nexus /var/backups/nexus
chmod 700 /etc/nexus /var/backups/nexus
install -m 644 "$ORIGEN/docker-compose.appliance.yml" "$DESTINO/docker-compose.appliance.yml"
install -m 755 "$ORIGEN"/scripts/*.sh "$DESTINO/scripts/"
ln -sf "$DESTINO/scripts/nexus-ctl.sh" /usr/local/bin/nexus-ctl
ln -sf "$DESTINO/scripts/nexus-update.sh" /usr/local/bin/nexus-update
install -m 644 "$ORIGEN"/systemd/* /etc/systemd/system/

echo "[6/9] Credenciales y variables"
PASSWORD_GENERADA=""
if [ ! -f "$ENV_DEST" ]; then
    install -m 600 "$ORIGEN/.env.appliance.example" "$ENV_DEST"
    fijar_var SECRET_KEY "$(openssl rand -hex 32)"
    fijar_var TOTP_ENCRYPTION_KEY "$(clave_base64)"
    fijar_var SOCIAL_TOKEN_ENCRYPTION_KEY "$(clave_base64)"
    fijar_var POSTGRES_PASSWORD "$(openssl rand -hex 24)"
    PASSWORD_GENERADA=${SUPERADMIN_PASSWORD:-"$(openssl rand -hex 8)Aa7-$(openssl rand -hex 8)"}
    fijar_var SUPERADMIN_PASSWORD "$PASSWORD_GENERADA"
    fijar_var CREAR_SUPER_ADMIN true
else
    echo "Ya existe $ENV_DEST: se conservan las claves y la base de datos actuales."
fi
chmod 600 "$ENV_DEST"

URL="https://$NEXUS_DOMAIN"
fijar_var GHCR_OWNER "$GHCR_OWNER"
fijar_var CLOUDFLARE_TUNNEL_TOKEN "$CLOUDFLARE_TUNNEL_TOKEN"
fijar_var PUBLIC_URL "$URL"
fijar_var CORS_ORIGINS "$URL"
fijar_var FRONTEND_BASE_URL "$URL"
fijar_var META_REDIRECT_URI "$URL/api/redes-sociales/callback/facebook"
fijar_var META_INSTAGRAM_REDIRECT_URI "$URL/api/redes-sociales/callback/instagram"
fijar_var TIKTOK_REDIRECT_URI "$URL/api/redes-sociales/callback/tiktok"
fijar_var GOOGLE_REDIRECT_URI "$URL/api/redes-sociales/callback/youtube"
fijar_var SUPERADMIN_USERNAME "$SUPERADMIN_USERNAME"
if [ -n "${HEARTBEAT_URL:-}" ]; then
    fijar_var HEARTBEAT_URL "$HEARTBEAT_URL"
fi
if [ -n "${ALERT_WEBHOOK_URL:-}" ]; then
    fijar_var ALERT_WEBHOOK_URL "$ALERT_WEBHOOK_URL"
fi
if [ -n "${TZ_LOCAL:-}" ]; then
    fijar_var TZ "$TZ_LOCAL"
    timedatectl set-timezone "$TZ_LOCAL" || true
fi

echo "[7/9] Descarga de imagenes"
if [ -n "${GHCR_TOKEN:-}" ]; then
    printf '%s' "$GHCR_TOKEN" | docker login ghcr.io -u "${GHCR_USER:-$GHCR_OWNER}" --password-stdin
fi
docker compose --env-file "$ENV_DEST" -f "$DESTINO/docker-compose.appliance.yml" pull
docker tag "ghcr.io/$GHCR_OWNER/nexus-api:stable" "ghcr.io/$GHCR_OWNER/nexus-api:previous"
docker tag "ghcr.io/$GHCR_OWNER/nexus-web:stable" "ghcr.io/$GHCR_OWNER/nexus-web:previous"

echo "[8/9] Arranque automatico"
systemctl daemon-reload
systemctl enable --now nexus-stack.service
systemctl enable --now nexus-update.timer nexus-backup.timer nexus-heartbeat.timer

echo "[9/9] Esperando a que la aplicacion responda"
. "$DESTINO/scripts/lib.sh"
if esperar_salud 300; then
    echo "Aplicacion saludable."
    if [ -n "$PASSWORD_GENERADA" ]; then
        fijar_var CREAR_SUPER_ADMIN false
        fijar_var SUPERADMIN_PASSWORD ""
    fi
else
    echo "La aplicacion no respondio a tiempo. Revisa: nexus-ctl logs api" >&2
    exit 1
fi

shred -u "$ENTRADA" 2>/dev/null || rm -f "$ENTRADA"

echo
echo "Instalacion terminada."
echo "Direccion publica: $URL"
if [ -n "$PASSWORD_GENERADA" ]; then
    echo "Usuario: $SUPERADMIN_USERNAME"
    echo "Contrasena inicial (anotala ahora, no se vuelve a mostrar): $PASSWORD_GENERADA"
fi
echo "Respalda FUERA del equipo la clave SOCIAL_TOKEN_ENCRYPTION_KEY de $ENV_DEST."
