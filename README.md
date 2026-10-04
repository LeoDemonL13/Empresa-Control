# Nexus Obsidian Control

Panel de escritorio y servidor para administrar hasta 100 equipos. Este paquete llega completo hasta la **Fase 6**: acceso, Administradores, Bitácora, Equipos, agente con señal de vida, la matriz de control de aplicaciones (permitir o bloquear, límites de tiempo diario, uso real), el Inicio con indicadores en vivo y el resumen de redes sociales, y el módulo de Reportes (general, actividades y uso, auditoría) en PDF, CSV y Excel.

## Inicio rápido en Windows

1. Instala **Docker Desktop** y **Node.js 22 LTS** (una sola vez).
2. Extrae el zip en una carpeta. No lo abras desde el explorador comprimido.
3. Haz doble clic en **`INICIAR_EN_PC.bat`**.

La primera vez el archivo te pide el usuario y la clave del súper administrador, genera solo las claves de seguridad, levanta el servidor, instala el panel y abre el navegador en http://localhost:5173 ya con la pantalla de inicio de sesión. En las siguientes veces arranca directo, sin preguntar nada.

- La clave que escribes se guarda en `nexus-control-api\.env` solo mientras se crea el usuario. En cuanto el servidor responde, el archivo la borra y desactiva la creación.
- Para apagar el servidor de fondo abre **`DETENER_EN_PC.bat`**. Los datos se conservan.
- Si algo falla, la ventana muestra los últimos mensajes del servidor y espera a que presiones una tecla.
- Para recuperar el acceso si olvidas la clave, pon en `nexus-control-api\.env`: `CREAR_SUPER_ADMIN=true`, `SUPERADMIN_USERNAME='tu-usuario'`, `SUPERADMIN_PASSWORD='nueva-clave'` y `SUPERADMIN_FORZAR_PASSWORD=true`; abre `INICIAR_EN_PC.bat` y el archivo vuelve a borrar la clave.

Lo demás de este documento es la referencia detallada y el método manual.

## Módulo de Equipos

- **Alta de equipos:** desde "Agregar equipo" en el panel. Al crear uno se genera un código de enrolamiento de un solo uso (válido 30 minutos) que después usará el agente de la Fase 3 para darse de alta. El código se muestra una sola vez.
- **Categorías:** se escriben como texto libre; si no existe una categoría con ese nombre (sin distinguir mayúsculas ni espacios de más), se crea sola.
- **Estado en línea:** se actualiza solo con la señal de vida (`heartbeat`) que manda el agente cada 30 segundos; si un equipo deja de mandarla por 90 segundos, el panel lo marca "Fuera de línea" sin que nadie tenga que hacer nada.
- **Código vencido o perdido:** abre el equipo con "Ver" y usa "Regenerar" (o "Generar código" si no hay uno activo); el anterior queda invalidado.

## Matriz de control de aplicaciones

Dentro de "Ver" en un equipo, la pestaña **Aplicaciones** muestra la matriz de control de ese equipo:

- **Agregar una aplicación** escribiendo el nombre de su ejecutable (por ejemplo `discord.exe`). Si el ejecutable no existe todavía en el catálogo general, se crea solo.
- **Permitida / Bloqueada:** un botón por aplicación. Al bloquear una, el agente del equipo la cierra automáticamente la próxima vez que la detecte corriendo (o al instante, si el equipo está conectado).
- **Sin límite / Con límite:** si se pone "Con límite", se indican los minutos permitidos al día; al alcanzarlos, el agente cierra la aplicación igual que si estuviera bloqueada. El límite se reinicia solo cada día.
- **Uso por aplicación:** debajo de cada fila se ve el tiempo usado hoy y en los últimos 7 días, con una barra comparando el consumo entre aplicaciones del mismo equipo.
- **Quitar una aplicación** de la matriz con el botón de basura; deja de controlarse pero su historial de uso no se borra.

Todo cambio en la matriz queda en la Bitácora y se envía al agente del equipo en vivo por WebSocket si está conectado; si no lo está, el agente la recibe en cuanto vuelve a conectarse.

## Inicio

La pantalla de Inicio muestra:

- **Indicadores en vivo:** equipos registrados, en línea, fuera de línea y aplicaciones bloqueadas. Se actualizan solos cuando cambia el estado de un equipo o se aplica una política, sin recargar la página.
- **Aplicaciones más usadas:** las 5 aplicaciones con más tiempo de uso en los últimos 7 días, en todo el parque de equipos.
- **Actividad reciente:** las últimas acciones del administrador que inició sesión.
- **Resumen de redes sociales:** tarjetas con métricas por plataforma (me gusta, interacciones, impresiones y engagement). Esta tabla empieza vacía a propósito: no hay datos de ejemplo. Con "Agregar" se escribe el nombre de la red social (si no existe, se crea sola, igual que las categorías) y se capturan los números reales; "Editar" permite corregirlos y el bote de basura la quita del resumen. Son datos que el equipo de marketing/community carga a mano, no una integración automática con ninguna red social.

## Módulo de Reportes

Desde "Reportes" se generan tres tipos de reporte, cada uno descargable en **PDF, CSV o Excel** con el membrete de Nexus Obsidian:

- **Reporte general:** inventario completo de equipos (categoría, usuario asignado, IP, MAC, hostname, sistema operativo, estado del agente, estado de conexión y fecha de alta).
- **Actividades y uso:** tiempo de uso de aplicaciones por equipo, con filtros de rango de fechas, equipo y categoría.
- **Auditoría:** el historial completo de la Bitácora, con filtros de rango de fechas, usuario, entidad y origen (panel, agente o sistema).

Cada descarga queda registrada en la Bitácora como cualquier otra acción del administrador.

## El agente

El agente es el programa que se instala en cada PC para que deje de aparecer "Fuera de línea". Vive en `nexus-control-agent/` y tiene su propio `INICIAR_AGENTE_EN_PC.bat` y README con el paso a paso.

Resumen: generas el código en el panel (Equipos → Agregar equipo), lo pegas una vez en el agente junto con la dirección del servidor, y el agente queda enrolado. Desde ahí manda su inventario básico y una señal de vida cada 30 segundos; si deja de mandarla por 90 segundos, el panel lo marca "Fuera de línea" solo. Además, aplica en el equipo la matriz de control de aplicaciones configurada en el panel: cierra lo que esté bloqueado o haya agotado su límite de tiempo, y reporta el uso real de cada aplicación.

Para probarlo en la misma PC donde corre el servidor, la dirección por defecto (`http://localhost:5001`) ya funciona. Para instalarlo en otra PC de la red, usa la IP de la PC del servidor en vez de `localhost`.

## Problemas comunes

**"La base de datos ya existía, creada con una contraseña distinta"** — pasa si antes abriste el proyecto desde otra carpeta o copia: Docker guarda la base de datos por separado del `.env`, así que si el `.env` es nuevo (otra carpeta) pero la base de datos es la de antes, las contraseñas no coinciden. `INICIAR_EN_PC.bat` ahora detecta esto solo y pregunta si quiere borrar esa base de datos anterior (sin datos importantes todavía) y reintentar; responde `S` y sigue automáticamente. Para que no vuelva a pasar, usa siempre esta misma carpeta para las próximas versiones en vez de extraerlas en una carpeta nueva cada vez.

## Qué incluye

| Carpeta | Contenido |
|---|---|
| `nexus-control-api/` | API Flask: fábrica de la app, extensiones, seguridad HTTP, límite de peticiones, CORS, Socket.IO, bitácora, migraciones Alembic, Docker (API + PostgreSQL + Redis), súper admin, login con JWT y 2FA, Administradores, Bitácora, Equipos y Categorías, los endpoints para el agente (enrolamiento, inventario, señal de vida), la matriz de control de aplicaciones (`/api/equipos/<id>/aplicaciones`, `/api/equipos/<id>/uso`) y sus endpoints para el agente (`/api/agente/politicas`, `/api/agente/uso`), el resumen del Inicio (`/api/dashboard/resumen`), las métricas de redes sociales (`/api/metricas-sociales`) y los reportes en PDF/CSV/Excel (`/api/reportes/general`, `/api/reportes/uso`, `/api/reportes/auditoria`). |
| `nexus-control-frontend/` | React + Vite + Tailwind. Login, 2FA, layout con menú lateral y búsqueda `⌘K`, Mi perfil, Administradores, Bitácora, Equipos (tarjetas, filtros, alta y código de enrolamiento, y la pestaña "Aplicaciones" con la matriz de control y el uso por aplicación), Inicio (indicadores en vivo y resumen de redes sociales) y Reportes (descarga de los tres reportes en PDF/CSV/Excel), todo reflejado en vivo cuando un agente real se conecta o reporta uso. |
| `nexus-control-agent/` | El programa en Python que se instala en cada equipo: se enrola con el código, manda su inventario y una señal de vida cada 30 segundos, aplica la matriz de control (bloqueo y límites de tiempo) y reporta el uso real de cada aplicación. Tiene su propio `INICIAR_AGENTE_EN_PC.bat` y README. |
| `INICIAR_EN_PC.bat` y `DETENER_EN_PC.bat` | Arrancan y apagan el panel y el servidor con doble clic. |
| `scripts/` | Script de PowerShell que crea el `.env` con claves aleatorias. |
| `docs/` | Capturas de las pantallas principales. |

## Requisitos

- Docker Desktop
- Node.js 22

## Método manual

Si prefieres no usar el `.bat`, estos son los pasos equivalentes.

## Paso 1. Levantar el servidor

Abre una terminal en `nexus-control-api`.

1. Copia el archivo de ejemplo:
   - Windows: `copy .env.example .env`
   - Mac o Linux: `cp .env.example .env`
2. Genera las dos claves secretas. Ejecuta este comando **dos veces** y usa un resultado para cada una:

   ```
   docker run --rm python:3.12-slim python -c "import base64,os;print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
   ```
3. Edita `.env` y completa:
   - `SECRET_KEY`: el primer resultado.
   - `TOTP_ENCRYPTION_KEY`: el segundo resultado.
   - `POSTGRES_PASSWORD`: una contraseña larga.
   - `SUPERADMIN_USERNAME`: el correo o usuario del súper administrador.
   - `SUPERADMIN_PASSWORD`: mínimo 12 caracteres, con mayúscula, minúscula, número y símbolo.
   - `SUPERADMIN_FULL_NAME`: tu nombre completo (opcional).
4. Levanta todo:

   ```
   docker compose up --build
   ```

En los registros debes ver, en este orden:

```
[entrypoint] La base de datos responde.
[bootstrap] Esquema creado y marcado en la última revisión.
[super_admin] tu-usuario | super_admin | creado
[entrypoint] Arrancando: gunicorn ...
```

No hay usuario ni contraseña por defecto. Si `CREAR_SUPER_ADMIN=true` y dejas `SUPERADMIN_USERNAME` o `SUPERADMIN_PASSWORD` vacíos, o la contraseña no cumple la política, el arranque se detiene con un mensaje `CRÍTICO` en los registros. Para levantar el servidor sin crear ningún usuario, pon `CREAR_SUPER_ADMIN=false`.

## Paso 2. Comprobar el servidor

Con el servidor en marcha, en otra terminal:

| Comprobación | Comando | Resultado esperado |
|---|---|---|
| Estado | `curl http://localhost:5001/health` | `{"status":"ok"}` |
| Error estandarizado | `curl http://localhost:5001/api/no-existe` | `{"error":"Recurso no encontrado."}` con código 404 |
| Cabeceras de seguridad | `curl -i http://localhost:5001/health` | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Cache-Control: no-store...` |
| Tablas creadas | `docker compose exec db psql -U nexus_control -d nexus_control -c "\dt"` | `users`, `audit_log`, `refresh_tokens`, `totp_backup_codes`, `alembic_version` |
| Súper admin | `docker compose exec db psql -U nexus_control -d nexus_control -c "select username, role, activo from users"` | Tu usuario con rol `super_admin` |

Si cambiaste `POSTGRES_USER` o `POSTGRES_DB`, usa esos valores en los comandos de `psql`.

## Paso 3. Ver el sistema de diseño

Abre una terminal en `nexus-control-frontend`:

```
npm install
npm run dev
```

Abre http://localhost:5173. Verás la guía de estilo con la paleta, la tipografía, los botones, los estados, las tarjetas KPI, la navegación lateral y la estructura de la tarjeta de equipo. El botón del sol o la luna, arriba a la derecha, alterna entre tema oscuro y claro.

Revisa especialmente:

- Que el menú lateral tenga el mismo tono borgoña del ERP.
- Que el botón principal sea una píldora roja que brilla al pasar el cursor.
- Que las etiquetas de sistema (`EN LÍNEA`, `SEC PROTECTED`) usen letra monoespaciada.

## Paso 4. Ejecutar las pruebas

Servidor (con los contenedores levantados):

```
docker compose run --rm api python -m pytest -q
```

Debes ver `179 passed`.

Frontend:

```
npm test
```

Debes ver `38 passed`.

Agente (ver el README de `nexus-control-agent/`): `33 passed`.

## Cambiar el rojo de la marca

Edita una línea en `nexus-control-frontend/src/index.css`:

```
--nx-accent: 239 31 43;
--nx-accent-strong: 220 23 36;
```

Los valores son RGB separados por espacios. Para `#E30613` usa `227 6 19`.

## Puertos

Para no chocar con el ERP si lo tienes corriendo al mismo tiempo:

| Servicio | Puerto |
|---|---|
| API | 5001 |
| PostgreSQL (solo desde tu equipo) | 5434 |
| Frontend en desarrollo | 5173 |

## Variables del súper administrador

| Variable | Efecto |
|---|---|
| `CREAR_SUPER_ADMIN=true` | Ejecuta el script en cada arranque. Es seguro dejarlo activo: si el usuario ya existe, no toca su contraseña. |
| `SUPERADMIN_FORZAR_PASSWORD=true` | Reemplaza la contraseña del usuario existente por la del `.env`, cierra sus sesiones y borra su 2FA. Úsalo solo para recuperar el acceso y vuelve a ponerlo en `false`. |
