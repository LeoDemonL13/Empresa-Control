# Nexus en un Mini PC "enchufar y listo" (appliance)

Esta guía convierte un Mini PC con Ubuntu Server en un equipo que:

- arranca solo cuando le regresa la luz,
- levanta Nexus sin que nadie inicie sesión,
- se publica en internet **sin abrir puertos, sin IP fija y aunque tu proveedor use CGNAT**,
- se actualiza solo cuando haces `git push` de una versión nueva, y **se revierte solo** si la versión nueva no funciona,
- te avisa si deja de dar señales de vida.

> **Alcance honesto.** Todo lo de esta guía se escribió y se validó con herramientas
> estáticas (compose, Caddy real, shellcheck, systemd-analyze) y con una simulación de la
> lógica de actualización/rollback. **No se probó en un Mini PC real, ni con un Docker real,
> ni contra Cloudflare/GitHub reales, ni el `.bat` en Windows.** Por eso la sección 8 es una
> batería de pruebas que debes hacer tú antes de dejar el equipo en producción.

---

## 1. Arquitectura

```
Internet ──► Cloudflare (HTTPS, dominio, DDoS) ◄── conexión SALIENTE ── cloudflared (contenedor)
                                                                              │
                                                                              ▼
                                  ┌──────────────── Mini PC (red interna de Docker) ────────────────┐
                                  │  web  = Caddy: sirve el frontend y reenvía /api y /socket.io     │
                                  │   │                                                              │
                                  │   ▼                                                              │
                                  │  api  = Flask + gunicorn + Socket.IO ──► db (Postgres) + redis   │
                                  └──────────────────────────────────────────────────────────────────┘

Administración remota: Tailscale (SSH) ─ solo tú, sin puertos abiertos
Actualizaciones:       git tag ─► GitHub Actions ─► imágenes en GHCR ─► el Mini PC las descarga
Monitoreo:             el Mini PC "late" cada minuto a Healthchecks.io; si deja de latir, te avisa
```

**Decisiones y por qué:**

| Decisión | Razón |
|---|---|
| Docker Compose (no systemd a pelo) | Mismo entorno que en tu PC, aislamiento, reinicio automático y rollback por etiqueta de imagen. |
| Caddy como única puerta de entrada | Un solo destino para el túnel; normaliza `X-Forwarded-For` y `X-Forwarded-Proto` (comprobado con el binario real). |
| Cloudflare Tunnel para la web | Conexión saliente: no necesita puertos, IP fija ni salir de CGNAT. |
| Tailscale para SSH | La administración no pasa por el dominio público. El firewall bloquea todo lo entrante salvo la red local (SSH) y Tailscale. |
| Actualizador propio en vez de Watchtower | Watchtower no hace rollback ni respalda la base antes de migrar. |
| `PROXY_FOR_HOPS=1` | Detrás de Caddy solo hay un salto de proxy visible para la app; sin esto, todos los clientes compartirían la misma IP y el mismo límite de intentos. Por defecto la app sigue usando 2 (no cambia nada en tu instalación actual). |

Archivos (todo en `deploy/appliance/`, más `.github/workflows/release-appliance.yml` e `INSTALAR_EN_MINIPC.bat` en la raíz):

| Archivo | Para qué |
|---|---|
| `docker-compose.appliance.yml` | Pila completa: api, web, tunnel, db, redis. |
| `web/Dockerfile`, `web/Caddyfile` | Imagen del frontend + proxy. |
| `.env.appliance.example` | Plantilla de variables (la rellena `provision.sh`). |
| `provision.sh` | Prepara el Ubuntu de cero: Docker, firewall, Tailscale, watchdog, red, claves, servicios. |
| `scripts/nexus-update.sh` | Actualiza con respaldo previo, verificación de salud y rollback. |
| `scripts/nexus-backup.sh` | Respaldo diario con rotación. |
| `scripts/nexus-heartbeat.sh` | Latido al monitor externo. |
| `scripts/nexus-ctl.sh` | Comando `nexus-ctl` para operar el equipo. |
| `systemd/*` | Arranque de la pila y temporizadores. |
| `netplan/01-nexus.yaml` | Red por DHCP que no bloquea el arranque si no hay cable. |

---

## 2. Qué necesitas antes de empezar

1. **Mini PC** (recomendado: procesador Intel N100 o superior, 16 GB RAM, SSD NVMe de 256–512 GB) y un cable de red. Un **UPS pequeño** es muy recomendable: el auto-encendido resuelve cortes de luz, pero un corte brusco repetido daña SSDs y bases de datos.
2. **Un dominio** administrado en Cloudflare (gratis: agrega el dominio a Cloudflare y cambia los DNS en tu registrador).
3. **Cuenta de GitHub** con este repositorio.
4. **Cuenta de Tailscale** (gratis) — [login.tailscale.com](https://login.tailscale.com).
5. **Cuenta de Healthchecks.io** (gratis) — o Uptime Kuma, si ya lo tienes.
6. Una memoria USB de 8 GB y otra PC para crearla.

---

### ¿Necesito un dominio?

**Sí, para el acceso público estable por HTTPS** (cuesta alrededor de 10–15 USD al año). Con él los equipos de los clientes, los celulares y los agentes se conectan desde cualquier lugar, sin abrir puertos. También es obligatorio para conectar redes sociales: Facebook, Instagram, TikTok y YouTube exigen una dirección HTTPS pública para el inicio de sesión.

Alternativas, con sus límites:

| Opción | Qué pasa |
|---|---|
| Solo red local (sin dominio) | Funciona con `http://IP_DEL_MINIPC`, solo dentro de la oficina. Las redes sociales no se podrían conectar. Esta variante no viene preparada en los archivos de esta guía. |
| Tailscale en todos los equipos | Sin dominio, pero cada PC y celular debe tener Tailscale instalado. No sirve para las redes sociales ni para páginas públicas de clientes. |
| Túnel rápido de Cloudflare (sin cuenta) | La dirección es aleatoria y cambia: no sirve para producción. |

El dominio no tiene que ser caro ni especial; cualquiera sirve si lo administras en Cloudflare. Las pruebas piloto de los agentes (`PRUEBA_PILOTO.md`) pueden hacerse en red local sin dominio.

---

## 3. Preparar el hardware

### 3.1 BIOS/UEFI (la parte que hace que "se encienda solo")

Entra a la BIOS (normalmente `Supr`, `F2` o `F7` al encender) y configura:

| Opción (el nombre varía según la marca) | Valor |
|---|---|
| **Restore on AC Power Loss** / **After Power Failure** / **AC Back** / **Power On after Power Failure** | **Power On** (o "Always On") |
| Wake on LAN / Power On by PCI-E | Enabled (útil para encenderlo a distancia) |
| Fast Boot | Disabled |
| Boot Order | El SSD primero (después de instalar) |
| Secure Boot | Puede quedar activado; Ubuntu lo soporta. Si el instalador no arranca, desactívalo |
| Hardware Watchdog / iTCO | Enabled, si aparece |

**Cómo comprobarlo:** guarda, apaga el equipo, **desconecta el cable de corriente 10 segundos**, vuelve a conectar. Debe encenderse solo, sin tocar el botón. Si no lo hace, esa opción no está bien configurada o tu modelo la llama distinto; no sigas hasta que funcione.

### 3.2 Instalar Ubuntu Server

1. Descarga **Ubuntu Server 24.04 LTS** desde ubuntu.com y grábalo en la USB (Rufus o balenaEtcher).
2. Arranca el Mini PC desde la USB e instala:
   - Idioma/teclado a tu gusto.
   - Red: déjala en **DHCP** (por cable).
   - Almacenamiento: "Use an entire disk" (puedes dejar LVM).
   - Crea un usuario administrador (por ejemplo `admin`) y una contraseña fuerte.
   - Activa **Install OpenSSH server**.
   - **No** instales ningún "featured snap" (Docker lo instala el script).
3. Reinicia, quita la USB y anota la IP local (`ip -4 addr` o míralo en tu router). Recomendado: en el router, reserva esa IP para el Mini PC (solo para comodidad; el sistema no la necesita).

---

## 4. Cuentas externas

### 4.1 Imágenes en GitHub (GHCR)

1. En GitHub: repositorio → **Settings → Actions → General** → permisos de workflow en **Read and write**.
2. Publica la primera versión (esto construye las imágenes):
   ```
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. Espera a que termine **Actions → release-appliance** (verde). Se crean `ghcr.io/<tu-usuario>/nexus-api` y `nexus-web` con la etiqueta `stable`.
4. Si el repositorio es privado, las imágenes también lo son: crea un **Personal access token (classic)** con permiso `read:packages` (GitHub → Settings → Developer settings). Lo usará el Mini PC para descargar.

### 4.2 Túnel de Cloudflare

1. Cloudflare → **Zero Trust** → **Networks → Tunnels → Create a tunnel** → tipo **Cloudflared**.
2. Nombre: `nexus-minipc`. En "Install connector" **no ejecutes nada**: solo copia el **token** (la cadena larga después de `--token`).
3. En la pestaña **Public Hostname** agrega:
   - Subdomain/Domain: por ejemplo `nexus.tudominio.com`
   - Service: tipo **HTTP**, URL **`web:80`**
4. Guarda. (Los WebSockets de Socket.IO funcionan por el túnel sin configuración extra.)

### 4.3 Tailscale (administración)

Tailscale admin → **Settings → Keys → Generate auth key** (marca *Reusable* si quieres reutilizarla; ponle expiración). Copia la clave `tskey-...`. Instala Tailscale también en tu PC para poder entrar por SSH.

### 4.4 Latido (Healthchecks.io)

1. Crea un check llamado `nexus-minipc` con **Period = 1 minuto** y **Grace = 5 minutos**.
2. Agrega tu correo (o Telegram/WhatsApp/Slack) como canal de aviso.
3. Copia la **Ping URL** (`https://hc-ping.com/xxxxxxxx-...`).

Qué cubre: si el Mini PC se apaga, pierde internet, el túnel se cae, la app deja de responder o el disco pasa de 90%, el latido deja de llegar (o llega como fallo) y recibes el aviso.

---

## 5. Instalar en el Mini PC

### Opción A — con el `.bat` desde tu PC con Windows

1. Doble clic en `INSTALAR_EN_MINIPC.bat` (necesita el cliente OpenSSH de Windows, que viene incluido en Windows 10/11).
2. Responde lo que pide: IP del Mini PC, usuario, dominio, usuario de GitHub, token del túnel, usuario/token de GitHub para descargar, clave de Tailscale, URL de latido y correo del super administrador.
3. Escribe la contraseña del usuario del Mini PC cuando `ssh` la pida (la pedirá varias veces, una por cada paso de conexión, y además la de `sudo`).
4. Al final verás la contraseña inicial del super administrador. **Anótala**: no se vuelve a mostrar.

### Opción B — a mano

```
scp -r deploy/appliance admin@IP_DEL_MINIPC:nexus-deploy
ssh admin@IP_DEL_MINIPC
sudo nano /root/nexus-provision.env
```

Contenido del archivo (valores entre comillas simples):

```
NEXUS_DOMAIN='nexus.tudominio.com'
GHCR_OWNER='tu-usuario-de-github'
CLOUDFLARE_TUNNEL_TOKEN='...'
SUPERADMIN_USERNAME='tu@correo.com'
GHCR_USER='tu-usuario-de-github'
GHCR_TOKEN='ghp_...'
TAILSCALE_AUTHKEY='tskey-...'
HEARTBEAT_URL='https://hc-ping.com/...'
ALERT_WEBHOOK_URL=''
TZ_LOCAL='America/Mexico_City'
```

Después: `sudo chmod 600 /root/nexus-provision.env && sudo bash ~/nexus-deploy/provision.sh`

**El script es repetible**: si lo vuelves a ejecutar conserva `/etc/nexus/.env` (claves y contraseñas) y la base de datos. Así también aplicas cambios a los scripts o al compose del appliance.

### Qué hace `provision.sh`

Instala actualizaciones de seguridad automáticas (con reinicio nocturno a las 04:30), Docker, red por DHCP que no bloquea el arranque, desactiva suspensión/hibernación, activa el watchdog de hardware del sistema (si el equipo lo tiene), journal persistente acotado, Tailscale, firewall (todo entrante bloqueado salvo Tailscale y SSH desde red local), genera claves seguras en `/etc/nexus/.env` (solo root), descarga las imágenes y deja activos el arranque automático y los temporizadores de actualización, respaldo y latido.

---

## 6. Redes sociales en el appliance

El script ya deja las cuatro URLs de redirección con tu dominio público. Solo falta registrarlas y pegar las credenciales:

1. Sigue `CONFIGURAR_REDES_SOCIALES.md`, usando como URL de redirección `https://tu-dominio/api/redes-sociales/callback/<plataforma>`.
2. En el Mini PC (por SSH): `sudo nano /etc/nexus/.env` y completa `META_APP_ID`, `META_APP_SECRET`, `TIKTOK_CLIENT_KEY`, etc.
3. Aplica: `sudo nexus-ctl aplicar` (`reiniciar` **no** vuelve a leer el archivo de variables; `aplicar` sí).
4. **Respalda fuera del equipo** `SOCIAL_TOKEN_ENCRYPTION_KEY` (de `/etc/nexus/.env`). Si el disco muere y no la tienes, las conexiones guardadas son irrecuperables y habrá que reconectar cada red.

---

## 7. Flujo de actualización (de `git push` al Mini PC)

```
git tag v1.2.0 && git push origin v1.2.0
        │
        ▼
GitHub Actions: pruebas backend ─┐
                pruebas frontend ┴─► si todo pasa: construye y publica nexus-api y nexus-web
                                     con etiquetas  :v1.2.0  :stable  :<sha>
        │
        ▼  (cada ~10 min, el Mini PC consulta; si :stable cambió:)
 1. respaldo de la base (pre-actualizacion-*.sql.gz). Si el respaldo falla, NO actualiza
 2. guarda las imágenes actuales como :previous
 3. recrea api y web con la imagen nueva (las migraciones corren en el arranque)
 4. espera hasta 4 min a que /health responda, y confirma otra vez a los 20 s
 5a. sano → listo, avisa, limpia imágenes viejas
 5b. no sano → vuelve a :previous; si la revisión de la base cambió, restaura el respaldo;
     marca la imagen mala para no reintentarla en bucle; avisa
```

- Push a `main` **sin etiqueta** publica solo `:edge` (el Mini PC no lo usa). Producción solo se mueve cuando creas una etiqueta `v*`. Si prefieres que cada `push` a `main` actualice el Mini PC, cambia en el workflow la lógica de etiquetas para que `main` también publique `:stable`.
- Para volver a intentar una versión que se marcó como mala, publica una corrección (otra etiqueta): el identificador de imagen será distinto.
- Cambios a `docker-compose.appliance.yml`, scripts o units **no** viajan por este flujo (solo imágenes). Para aplicarlos: vuelve a ejecutar la instalación (sección 5), que es repetible y no toca tus datos.
- Actualización manual inmediata: `sudo nexus-ctl actualizar`.

---

## 8. Pruebas (hazlas todas antes de producción)

Entra por SSH al Mini PC (con Tailscale: `ssh admin@nexus-minipc`).

**P1 — La instalación quedó sana**
1. `sudo nexus-ctl estado`
2. Debes ver 5 contenedores `running` (db y redis `healthy`), `App: OK`, `Tunel: OK` y una revisión de base.
3. Desde tu PC o celular (con datos móviles, fuera de tu red) abre `https://tu-dominio`. Inicia sesión con el super administrador.
4. Falla típica: "Tunel: SIN CONEXION" → el token está mal o el Public Hostname apunta a otra URL distinta de `web:80`. Revisa con `sudo docker compose --env-file /etc/nexus/.env -f /opt/nexus/docker-compose.appliance.yml logs tunnel`.

**P2 — Corte de luz**
1. Con el sistema funcionando, **desconecta el cable de corriente** (no hagas apagado normal).
2. Conéctalo de nuevo. No toques ningún botón.
3. En 2–4 minutos `https://tu-dominio` debe abrir otra vez, y `nexus-ctl estado` debe estar sano.
4. Si no enciende: BIOS (sección 3.1). Si enciende pero no abre la web: `journalctl -u nexus-stack -b`.

**P3 — Se cae un contenedor**
1. `sudo docker kill nexus-api-1`
2. Espera 1 minuto: Docker lo reinicia solo (`restart: unless-stopped`). Confirma con `nexus-ctl estado`.

**P4 — Se va el internet**
1. Desconecta el cable de red del Mini PC 5 minutos y vuélvelo a conectar.
2. En ~1–2 minutos el túnel se reconecta solo y la web vuelve. El latido deja de llegar mientras no hay internet (Healthchecks te avisa tras el tiempo de gracia).

**P5 — Latido y alerta**
1. En Healthchecks el check debe estar en verde ("up").
2. Apaga el Mini PC desde el cable de corriente y espera el tiempo de gracia (5 min): debes recibir el aviso. Vuelve a conectar y comprueba que regresa a verde.

**P6 — Actualización sana**
1. Haz un cambio pequeño (por ejemplo un texto) y publica `git tag v1.0.1 && git push origin v1.0.1`.
2. Espera a que Actions termine en verde.
3. En el Mini PC: `sudo nexus-ctl actualizar` (o espera ≤10 min) y observa `journalctl -t nexus -f`. Debe aparecer "completada y saludable".
4. Recarga la web y confirma el cambio.

**P7 — Actualización mala → rollback**
> Esta prueba publica a propósito una imagen defectuosa como `:stable`. Hazla en una sola máquina y con tiempo.
1. En una PC con Docker, ingresa a GHCR (`docker login ghcr.io -u TU_USUARIO`) y ejecuta:
   ```
   mkdir mala && cd mala
   printf 'FROM ghcr.io/TU_USUARIO/nexus-api:stable\nCMD ["python","-c","import sys; sys.exit(1)"]\n' > Dockerfile
   docker build -t ghcr.io/TU_USUARIO/nexus-api:stable .
   docker push ghcr.io/TU_USUARIO/nexus-api:stable
   ```
2. En el Mini PC: `sudo nexus-ctl actualizar`.
3. Resultado esperado: tras ~4 minutos aparece "no quedó saludable, revirtiendo" y luego "rollback exitoso"; la web sigue funcionando con la versión anterior; llega el aviso (si configuraste webhook).
4. Repite `sudo nexus-ctl actualizar`: no debe reintentar esa imagen (el log queda en silencio).
5. Restablece publicando una etiqueta buena (`v1.0.2`).
6. Esta prueba no ejercita la restauración de la base (la revisión no cambia); esa rama solo se probó en la simulación.

**P8 — Respaldo y restauración**
1. `sudo nexus-ctl respaldar` y `sudo nexus-ctl respaldos`.
2. Crea un dato de prueba en la web (por ejemplo, un equipo nuevo).
3. `sudo nexus-ctl restaurar /var/backups/nexus/nexus-AAAAMMDD-HHMMSS.sql.gz` (escribe `RESTAURAR`).
4. El dato de prueba debe haber desaparecido y la web volver a abrir.

**P9 — Nada expuesto**
Desde otra PC de tu red: `nmap -p 1-10000 IP_DEL_MINIPC`. Solo debe aparecer el 22 (SSH, permitido desde la red local). Los puertos 80/443 no deben estar abiertos.

**P10 — IP real del cliente (límite de intentos)**
1. Desde dos redes distintas (WiFi y datos móviles) intenta iniciar sesión con contraseña incorrecta repetidamente desde una hasta que la app te bloquee temporalmente.
2. La otra red debe poder seguir intentándolo (cada IP tiene su propio contador). Si ambas se bloquean a la vez, la app no está viendo IP distintas: revisa `PROXY_FOR_HOPS=1` y los logs de acceso de `api`.

---

## 9. Operación diaria

| Quiero... | Comando (en el Mini PC) |
|---|---|
| Ver estado | `sudo nexus-ctl estado` |
| Ver logs | `sudo nexus-ctl logs api` (o `web`, `tunnel`, `db`) |
| Forzar actualización | `sudo nexus-ctl actualizar` |
| Respaldar ahora / listar | `sudo nexus-ctl respaldar` / `sudo nexus-ctl respaldos` |
| Aplicar cambios del `.env` | `sudo nexus-ctl aplicar` |
| Reiniciar todo | `sudo nexus-ctl reiniciar` |
| Historial de actualizaciones | `journalctl -t nexus --since "7 days ago"` |
| Último fallo de una actualización | `/var/lib/nexus/ultimo_fallo_api.log` |

---

## 10. Límites y riesgos que debes conocer

- **No probado en hardware real** ni con Docker/Cloudflare/GitHub reales (ver aviso al inicio). El `.bat` tampoco se probó en Windows.
- **Los respaldos están en el mismo disco.** Protegen contra un error de actualización o de usuario, **no** contra un SSD muerto o un robo. Copia periódicamente `/var/backups/nexus` a otro lugar (por ejemplo con `rclone` a un almacenamiento en la nube) — no está automatizado.
- **Dependencia de Cloudflare y de tu dominio.** Si Cloudflare cae, la web pública cae; el SSH por Tailscale sigue disponible. Cloudflare Tunnel gratuito sirve para tráfico web; no uses este túnel para transmitir video de cámaras.
- **Cloudflare ve el tráfico** (termina el HTTPS). Es la contrapartida de no abrir puertos.
- **El token del túnel está en las variables del contenedor `api`** (comparten `/etc/nexus/.env`). Es un riesgo menor, pero si un día quieres aislarlo, sepáralo en otro archivo.
- **Un corte de luz sin UPS** es recuperable (Postgres hace recuperación al arrancar), pero cada corte brusco es un riesgo para el disco.
- Mientras tu app de Meta/TikTok/Google esté en modo desarrollo, rigen las limitaciones descritas en `CONFIGURAR_REDES_SOCIALES.md`.
- `cloudflared` usa la etiqueta `latest`; si quieres fijar la versión, cambia la imagen en el compose y re-ejecuta la instalación.
