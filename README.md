# Nexus Obsidian Control

Panel de escritorio y servidor para administrar hasta 100 equipos, ahora también celulares y tablets Android. Este paquete llega completo hasta la **Fase 8**: acceso, Administradores, Bitácora, Equipos (PC y Android en una sola lista, con hostname/IP/sistema operativo que el agente completa solo), agente de Windows con señal de vida, agente de Android con bloqueo por pantalla, la matriz de control de aplicaciones (permitir o bloquear, límites de tiempo diario, uso real) compartida entre ambos tipos de equipo, el Inicio con indicadores en vivo, el resumen de redes sociales (manual o sincronizado solo), la nueva sección de **Redes sociales** para conectar Facebook, Instagram, TikTok, YouTube y X, y el módulo de Reportes (general, actividades y uso, auditoría) en PDF, CSV y Excel.

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

- **PC o Android:** al crear un equipo se elige el tipo. Ambos comparten la misma lista, la misma matriz de control de aplicaciones, el mismo Inicio y los mismos Reportes; la columna "Tipo" los distingue en todas las pantallas.
- **Alta de equipos:** desde "Agregar equipo" en el panel. Al crear uno se genera un código de enrolamiento de un solo uso (válido 30 minutos) que después usará el agente (de Windows o de Android, según el tipo elegido) para darse de alta. El código se muestra una sola vez.
- **Hostname, IP y sistema operativo:** ya no se escriben a mano al crear ni al editar un equipo. En cuanto el agente se enrola con el código, los reporta solo (lo mismo que ya hacía antes para marcar "En línea"); se ven como solo lectura en la pestaña "Información" de cada equipo.
- **Categorías:** se escriben como texto libre; si no existe una categoría con ese nombre (sin distinguir mayúsculas ni espacios de más), se crea sola.
- **Estado en línea:** se actualiza solo con la señal de vida (`heartbeat`) que manda el agente cada 30 segundos; si un equipo deja de mandarla por 90 segundos, el panel lo marca "Fuera de línea" sin que nadie tenga que hacer nada.
- **Código vencido o perdido:** abre el equipo con "Ver" y usa "Regenerar" (o "Generar código" si no hay uno activo); el anterior queda invalidado.

## Matriz de control de aplicaciones

Dentro de "Ver" en un equipo, la pestaña **Aplicaciones** muestra la matriz de control de ese equipo:

- **Agregar una aplicación** escribiendo el nombre de su ejecutable (por ejemplo `discord.exe`) en un PC, o el nombre del paquete en un Android (por ejemplo `com.instagram.android`). Si todavía no existe en el catálogo general, se crea solo. En un equipo Android que ya sincronizó su inventario de apps instaladas, se puede elegir de una lista en vez de escribir el nombre del paquete a mano.
- **Permitida / Bloqueada:** un botón por aplicación. En un PC, el agente la cierra automáticamente la próxima vez que la detecte corriendo (o al instante, si el equipo está conectado). En un Android, en cuanto la persona la abre le aparece una pantalla que explica el bloqueo y la regresa sola al inicio, ya que Android no permite cerrar otra app a la fuerza sin permisos de administrador del dispositivo.
- **Sin límite / Con límite:** si se pone "Con límite", se indican los minutos permitidos al día; al alcanzarlos, se bloquea igual que si estuviera bloqueada (cerrándola en un PC, o con la pantalla de bloqueo en un Android). El límite se reinicia solo cada día.
- **Uso por aplicación:** debajo de cada fila se ve el tiempo usado hoy y en los últimos 7 días, con una barra comparando el consumo entre aplicaciones del mismo equipo.
- **Quitar una aplicación** de la matriz con el botón de basura; deja de controlarse pero su historial de uso no se borra.

Todo cambio en la matriz queda en la Bitácora y se envía al agente del equipo en vivo por WebSocket si está conectado; si no lo está, el agente la recibe en cuanto vuelve a conectarse.

## Inicio

La pantalla de Inicio muestra:

- **Indicadores en vivo:** equipos registrados, en línea, fuera de línea y aplicaciones bloqueadas. Se actualizan solos cuando cambia el estado de un equipo o se aplica una política, sin recargar la página.
- **Aplicaciones más usadas:** las 5 aplicaciones con más tiempo de uso en los últimos 7 días, en todo el parque de equipos.
- **Actividad reciente:** las últimas acciones del administrador que inició sesión.
- **Resumen de redes sociales:** tarjetas con métricas por plataforma (me gusta, interacciones, impresiones y engagement). Esta tabla empieza vacía a propósito: no hay datos de ejemplo. Cada tarjeta dice si el número es "Manual" (lo cargó una persona con "Agregar"/"Editar") o "Automático" (lo trajo la sincronización real descrita abajo, en **Redes sociales**). Un valor manual se puede seguir editando o quitando con el bote de basura en cualquier momento.

## Redes sociales (sincronización automática)

En el menú lateral, **Redes sociales** permite conectar de verdad Facebook, Instagram, TikTok, YouTube y X: se pegan las credenciales de cada plataforma **una sola vez**, quedan cifradas en el servidor, y a partir de ahí el sistema sincroniza solo las métricas cada cierto tiempo, sin volver a pedirlas. El resultado aparece en el Inicio, en la tarjeta de esa red social, marcado como "Automático".

**Quién puede hacer qué:**

- Cualquier administrador puede ver el estado de las conexiones, sincronizar una plataforma o todas con el botón correspondiente.
- Solo el **súper administrador** puede guardar o quitar credenciales (son datos sensibles). Si un administrador normal entra a esta pantalla, no ve los botones de "Configurar" ni "Desconectar", solo "Sincronizar ahora".

**Cómo se sincroniza:**

- Automático: el servidor revisa todas las plataformas conectadas cada `INTERVALO_SINCRONIZACION_REDES_MINUTOS` minutos (60 por defecto). Se cambia en el `.env` del servidor.
- Manual: el botón "Sincronizar ahora" de cada tarjeta, o "Sincronizar todas" arriba de la lista, lo hace al instante — es la forma de comprobar que unas credenciales recién guardadas funcionan, sin esperar a la siguiente vuelta automática.
- Para apagar la sincronización automática por completo (dejando solo el botón manual), pon `SINCRONIZAR_REDES_SOCIALES=false` en el `.env` del servidor.

**Si algo falla:** la tarjeta de esa plataforma muestra el mensaje de error exacto que devolvió la red social (token vencido, permiso revocado, ID equivocado, etc.) en "Último error". Vuelve a guardar las credenciales correctas y sincroniza de nuevo.

### Cómo obtener las credenciales de cada plataforma

Estas credenciales las genera cada red social desde su propio sitio de desarrolladores; Nexus Obsidian Control no puede crearlas por ti porque están ligadas a la identidad y a las páginas/cuentas de tu negocio.

**Facebook** (campos: *Token de acceso de la página* e *ID de la página*)

1. Entra a [developers.facebook.com](https://developers.facebook.com), crea una app de tipo "Negocios".
2. En **Graph API Explorer**, selecciona tu app, pide un token de usuario con los permisos `pages_read_engagement` y `pages_show_list`, y cámbialo por un **token de página** de larga duración (el propio Graph API Explorer tiene un botón para esto, o se hace con el endpoint `/oauth/access_token` usando tu App ID y App Secret).
3. El **ID de la página** aparece en "Acerca de" de tu página de Facebook, o con `GET /me/accounts` usando tu token de usuario.

**Instagram** (campos: *Token de acceso* e *ID de la cuenta de Instagram Business*)

1. Tu cuenta de Instagram debe ser "Business" o "Creator" y estar vinculada a una página de Facebook (Instagram → Configuración → Cuentas vinculadas).
2. Usa el **mismo token de página** que obtuviste para Facebook arriba (necesita además el permiso `instagram_basic` e `instagram_manage_insights`).
3. El **ID de la cuenta de negocio** se obtiene con `GET /{id-de-tu-pagina}?fields=instagram_business_account` usando ese mismo token.

**TikTok** (campos: *Client Key*, *Client Secret*, *Refresh Token*)

1. Crea una cuenta en [developers.tiktok.com](https://developers.tiktok.com) y una app con el producto **Login Kit**, con los scopes `user.info.basic` y `user.info.stats`.
2. El **Client Key** y **Client Secret** se ven en el panel de la app.
3. El **Refresh Token** solo se consigue completando una vez el inicio de sesión de TikTok con esa app (es un paso interactivo de OAuth que TikTok exige; no hay forma de evitarlo la primera vez). El refresh token dura aproximadamente un año y Nexus Obsidian Control lo usa para renovar el token de acceso solo en cada sincronización, así que después de este paso único ya no se vuelve a pedir nada.

**YouTube** (campos: *Clave de API* e *ID del canal*)

1. Entra a [console.cloud.google.com](https://console.cloud.google.com), crea un proyecto, y en "APIs y servicios" activa **YouTube Data API v3**.
2. En "Credenciales", crea una **clave de API** (no hace falta OAuth para esto).
3. El **ID del canal** (empieza con `UC...`) se ve en YouTube Studio → Configuración → Canal → Información básica del canal.

**X (antes Twitter)** (campos: *Bearer Token* y *usuario de la cuenta*)

1. Entra a [developer.x.com](https://developer.x.com) y suscríbete a un plan con acceso a la API v2 (al menos el nivel "Basic", de pago; el nivel gratuito no permite leer tweets de una cuenta).
2. Crea una app y copia su **Bearer Token** (token de solo-app, no hace falta OAuth de usuario).
3. El campo "usuario" es el nombre de la cuenta sin el `@` (por ejemplo `mi_empresa`).

### Qué significa cada número por plataforma

La sincronización usa, para cada plataforma, los campos que su API pública realmente expone — no son los mismos conceptos exactos en todas, así que aquí está el mapeo real para leer bien las tarjetas:

| Plataforma | Me gusta | Interacciones | Impresiones |
|---|---|---|---|
| Facebook | Total de "Me gusta" de la página | Interacciones con publicaciones (28 días) | Impresiones de la página (28 días) |
| Instagram | Seguidores de la cuenta | Cuentas alcanzadas con interacción (28 días) | Alcance (28 días) |
| TikTok | Total histórico de "me gusta" de la cuenta | No disponible con la API gratuita (queda en 0) | No disponible con la API gratuita (queda en 0) |
| YouTube | Suma de "me gusta" de los últimos 10 videos | Me gusta + comentarios de esos mismos videos | Vistas de esos mismos videos |
| X | Suma de "me gusta" de las últimas 10 publicaciones | Me gusta + retweets + respuestas + citas de esas publicaciones | Impresiones de esas publicaciones (si tu nivel de API las incluye) |

**Dos límites honestos que hay que conocer:**

- **TikTok:** su API gratuita (Login Kit / Display API) no expone interacciones ni impresiones a nivel de cuenta, solo seguidores, videos y el total de "me gusta" acumulado. Para tener esos otros dos números haría falta la TikTok for Business API con una cuenta de anuncios, que es un proceso de aprobación distinto y más lento.
- **Meta (Facebook/Instagram) cambia de vez en cuando los nombres de sus métricas de Insights.** Si una tarjeta muestra un error mencionando una métrica desconocida o dada de baja, es casi seguro que Meta renombró o retiró ese nombre; revisa la documentación vigente de "Page Insights" o "Instagram Insights" en [developers.facebook.com](https://developers.facebook.com/docs/graph-api) y, si cambió, es un solo nombre a actualizar en `nexus-control-api/app/services/redes_sociales/meta.py` (las constantes `METRICA_IMPRESIONES_PAGINA`, `METRICA_INTERACCIONES_PAGINA`, `METRICA_ALCANCE_INSTAGRAM` y `METRICA_CUENTAS_ALCANZADAS_INSTAGRAM`, al principio del archivo).

Este mapeo se construyó a partir de la documentación pública de cada API (no hubo manera de probarlo contra las redes sociales reales durante el desarrollo, porque este entorno no tiene salida a esos servidores). La primera sincronización real que hagas, con tus propias credenciales, es la verdadera prueba; si algo no calza, el mensaje de "Último error" de la tarjeta trae la respuesta exacta de la plataforma para saber qué ajustar.

## Módulo de Reportes

Desde "Reportes" se generan tres tipos de reporte, cada uno descargable en **PDF, CSV o Excel** con el membrete de Nexus Obsidian:

- **Reporte general:** inventario completo de equipos (categoría, usuario asignado, IP, MAC, hostname, sistema operativo, estado del agente, estado de conexión y fecha de alta).
- **Actividades y uso:** tiempo de uso de aplicaciones por equipo, con filtros de rango de fechas, equipo y categoría.
- **Auditoría:** el historial completo de la Bitácora, con filtros de rango de fechas, usuario, entidad y origen (panel, agente o sistema).

Cada descarga queda registrada en la Bitácora como cualquier otra acción del administrador.

## El agente de Windows

El agente es el programa que se instala en cada PC para que deje de aparecer "Fuera de línea". Vive en `nexus-control-agent/` y tiene su propio `INICIAR_AGENTE_EN_PC.bat` y README con el paso a paso.

Resumen: generas el código en el panel (Equipos → Agregar equipo), lo pegas una vez en el agente junto con la dirección del servidor, y el agente queda enrolado. Desde ahí manda su inventario básico y una señal de vida cada 30 segundos; si deja de mandarla por 90 segundos, el panel lo marca "Fuera de línea" solo. Además, aplica en el equipo la matriz de control de aplicaciones configurada en el panel: cierra lo que esté bloqueado o haya agotado su límite de tiempo, y reporta el uso real de cada aplicación.

Para probarlo en la misma PC donde corre el servidor, la dirección por defecto (`http://localhost:5001`) ya funciona. Para instalarlo en otra PC de la red, usa la IP de la PC del servidor en vez de `localhost`.

**Corrección en esta entrega:** al diseñar el envío de uso del agente de Android se encontró que el agente de Windows reenviaba, en cada sincronización (cada minuto), el total acumulado del día completo en vez de solo lo nuevo desde el envío anterior, y el servidor lo sumaba encima de lo ya guardado. El efecto era que, cuanto más tiempo llevara un agente corriendo sin reiniciarse, más se inflaban los minutos de uso reportados en el panel respecto al tiempo real. Ya está corregido (ahora el agente solo envía lo nuevo desde el último envío exitoso) y se agregaron dos pruebas que verifican que no vuelva a pasar.

## El agente de Android

Hace lo mismo que el agente de Windows, pero para celulares y tablets Android: se enrola con un código, reporta el equipo al panel y aplica la matriz de control. Como Android no permite cerrar otra app a la fuerza, el bloqueo se hace con una pantalla propia de Nexus Obsidian que explica el motivo y regresa sola al inicio.

Vive en `nexus-control-android/`, es un proyecto de Android Studio (Kotlin) y tiene su propio README con las instrucciones completas para compilarlo, instalarlo y probarlo, además de un flujo de GitHub Actions que lo compila y le corre las pruebas automáticamente. A diferencia del resto de este paquete, este módulo no pudo compilarse ni probarse en vivo durante su desarrollo por no tener, en ese entorno, acceso a los servidores de Google ni al SDK de Android; su README explica con detalle qué sí se verificó y cómo comprobar el resto.

## Problemas comunes

**"La base de datos ya existía, creada con una contraseña distinta"** — pasa si antes abriste el proyecto desde otra carpeta o copia: Docker guarda la base de datos por separado del `.env`, así que si el `.env` es nuevo (otra carpeta) pero la base de datos es la de antes, las contraseñas no coinciden. `INICIAR_EN_PC.bat` ahora detecta esto solo y pregunta si quiere borrar esa base de datos anterior (sin datos importantes todavía) y reintentar; responde `S` y sigue automáticamente. Para que no vuelva a pasar, usa siempre esta misma carpeta para las próximas versiones en vez de extraerlas en una carpeta nueva cada vez.

## Qué incluye

| Carpeta | Contenido |
|---|---|
| `nexus-control-api/` | API Flask: fábrica de la app, extensiones, seguridad HTTP, límite de peticiones, CORS, Socket.IO, bitácora, migraciones Alembic, Docker (API + PostgreSQL + Redis), súper admin, login con JWT y 2FA, Administradores, Bitácora, Equipos (PC y Android) y Categorías, los endpoints para el agente (enrolamiento, inventario, señal de vida, catálogo de apps instaladas), la matriz de control de aplicaciones (`/api/equipos/<id>/aplicaciones`, `/api/equipos/<id>/uso`) y sus endpoints para el agente (`/api/agente/politicas`, `/api/agente/uso`, `/api/agente/apps-instaladas`), el resumen del Inicio (`/api/dashboard/resumen`), las métricas de redes sociales (`/api/metricas-sociales`), las conexiones y la sincronización automática de redes sociales (`/api/conexiones-sociales`, cifrado de credenciales, clientes de Facebook/Instagram/TikTok/YouTube/X y el programador en segundo plano) y los reportes en PDF/CSV/Excel (`/api/reportes/general`, `/api/reportes/uso`, `/api/reportes/auditoria`). |
| `nexus-control-frontend/` | React + Vite + Tailwind. Login, 2FA, layout con menú lateral y búsqueda `⌘K`, Mi perfil, Administradores, Bitácora, Equipos (tarjetas, filtros, alta con selector de tipo PC/Android y código de enrolamiento — el hostname/IP/sistema operativo ya no se escriben a mano —, y la pestaña "Aplicaciones" con la matriz de control, el catálogo de apps instaladas en Android y el uso por aplicación), Inicio (indicadores en vivo y resumen de redes sociales, manual o automático), **Redes sociales** (conectar Facebook/Instagram/TikTok/YouTube/X, ver su estado y sincronizar) y Reportes (descarga de los tres reportes en PDF/CSV/Excel), todo reflejado en vivo cuando un agente real se conecta o reporta uso. |
| `nexus-control-agent/` | El programa en Python que se instala en cada PC: se enrola con el código, manda su inventario y una señal de vida cada 30 segundos, aplica la matriz de control (bloqueo y límites de tiempo) y reporta el uso real de cada aplicación. Tiene su propio `INICIAR_AGENTE_EN_PC.bat` y README. |
| `nexus-control-android/` | Proyecto de Android Studio (Kotlin) que se instala en celulares y tablets: se enrola con el código, sube su inventario y el catálogo de apps instaladas, y aplica la matriz de control con una pantalla de bloqueo propia de Nexus Obsidian. Tiene su propio README, un `INSTALAR_APK_EN_PC.bat` y un flujo de GitHub Actions que lo compila y le corre las pruebas. |
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

Debes ver `228 passed`.

Frontend:

```
npm test
```

Debes ver `48 passed`.

Agente de Windows (ver el README de `nexus-control-agent/`): `35 passed`.

Agente de Android (ver el README de `nexus-control-android/`): pruebas JUnit de `PoliticaTest` y `CalculoUsoTest`; no se pudieron ejecutar en este entorno por no tener SDK de Android, pero sí se verificó la misma lógica con el compilador de Kotlin por separado, y quedan listas para correr solas en Android Studio o en GitHub Actions.

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
