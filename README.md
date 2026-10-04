# Nexus Obsidian Control

Panel de escritorio y servidor para administrar hasta 100 equipos, ahora también celulares y tablets Android. Este paquete llega completo hasta la **Fase 8**: acceso, Administradores, Bitácora, Equipos (PC y Android en una sola lista, con hostname/IP/sistema operativo que el agente completa solo), agente de Windows con señal de vida, agente de Android con bloqueo por pantalla, la matriz de control de aplicaciones (permitir o bloquear, límites de tiempo diario, uso real) compartida entre ambos tipos de equipo, el Inicio con indicadores en vivo, el resumen de redes sociales (manual o sincronizado solo), la sección de **Redes sociales** para conectar Facebook, Instagram, TikTok y YouTube con el inicio de sesión real de cada plataforma (OAuth 2.0, sin pegar tokens a mano), y el módulo de Reportes (general, actividades y uso, auditoría) en PDF, CSV y Excel.

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

## Redes sociales (conexión real con OAuth)

En el menú lateral, **Redes sociales** conecta de verdad Facebook, Instagram, TikTok y YouTube: ya no se pega ningún token ni contraseña a mano. Cada tarjeta tiene un botón "Conectar con..." que abre el inicio de sesión real de esa plataforma (OAuth 2.0): la persona entra con su propia cuenta, autoriza el acceso, y la plataforma devuelve a Nexus Obsidian Control con un código de un solo uso que el servidor cambia por un token — ese token nunca pasa por el navegador ni se muestra en ninguna pantalla. Las credenciales quedan cifradas en el servidor (AES-256-GCM) y, desde ese momento, el sistema sincroniza solo las métricas cada cierto tiempo, renovando el acceso antes de que expire.

**Muy importante: una tarjeta solo se marca como conectada cuando la conexión es real.** Eso quiere decir que la persona completó el inicio de sesión de la plataforma, el servidor guardó el token cifrado, hizo una llamada de prueba real contra la API de esa red, y la plataforma identificó la cuenta externa (página, canal o usuario). Si cualquiera de esos pasos falla, la tarjeta se queda en gris o en rojo; nunca se simula una conexión.

**Quién puede hacer qué:**

- Cualquier administrador puede ver el estado de las conexiones, abrir el panel "Administrar" (en modo de solo lectura), sincronizar una plataforma o todas, y ver los resúmenes de actividad.
- Solo el **súper administrador** puede conectar, reconectar o desconectar una plataforma. Un administrador normal no ve esos botones, solo "Sincronizar ahora".

**Cómo conectar una plataforma:** antes de poder pulsar "Conectar con...", hay que dar de alta, una sola vez, una "aplicación" en el panel de desarrolladores de esa red social y copiar sus identificadores al `.env` del servidor — es un trámite de la propia red social, no algo que Nexus Obsidian Control pueda generar por ti. El archivo **[`CONFIGURAR_REDES_SOCIALES.md`](CONFIGURAR_REDES_SOCIALES.md)**, en la raíz de este proyecto, explica ese trámite paso a paso para las cuatro plataformas, sin dar por hecho que sabes de desarrollo. Mientras una plataforma no tenga esas variables configuradas, su tarjeta muestra un aviso en vez del botón de conectar, y el resto del sistema sigue funcionando con normalidad.

**Los 5 estados de una conexión:**

| Icono | Estado | Qué significa |
|---|---|---|
| 🟢 | Conectado | Todo funciona con normalidad. |
| 🔵 | Renovando sesión | El sistema está cambiando el token vencido por uno nuevo; es automático y ocurre en segundo plano. |
| 🟠 | La sesión está por expirar | El token todavía sirve, pero queda poco tiempo; el sistema lo va a renovar solo antes de que se acabe. |
| 🔴 | Requiere reconexión / Error | O la plataforma revocó el permiso (hay que pulsar "Reconectar"), o falló una sincronización y el sistema reintentará solo, con espera creciente (1, 2, 5, 15 y 30 minutos), sin desconectar la cuenta por un solo fallo. |
| ⚫ | No conectado | Nunca se conectó, o se desconectó a propósito. |

**Cómo se sincroniza:** el servidor revisa, cada minuto, qué conexiones ya les toca sincronizar según `SOCIAL_SYNC_INTERVAL_MINUTES` (15 minutos por defecto; se cambia en el `.env` del servidor), y sincroniza solo esas — no todas a la vez. El botón "Sincronizar ahora" de cada tarjeta, o "Sincronizar todas" arriba de la lista, lo hace al instante, útil para comprobar que una conexión recién hecha funciona sin esperar a la siguiente vuelta automática. Por seguridad hay un enfriamiento de un minuto entre dos sincronizaciones de la misma plataforma.

**El panel "Administrar"** de cada tarjeta muestra, sin mostrar nunca el token: la cuenta externa conectada (y quién la conectó, y cuándo), la lista de páginas/canales/cuentas encontradas con un interruptor para seguir o dejar de seguir cada una, la próxima sincronización programada, el último error en palabras simples (el detalle técnico completo solo queda en la Bitácora) y, para el súper administrador, los botones de reconexión o desconexión.

**El panel de estado del sistema**, arriba de la lista de tarjetas, muestra el intervalo de sincronización configurado y, por plataforma, el resultado y el tiempo de respuesta de la última sincronización — así se ve de un vistazo si todo el sistema de sincronización está funcionando, no solo una tarjeta.

**Resúmenes de actividad:** el panel calcula automáticamente totales de las últimas 24 horas, 7 días y 30 días (o un rango de fechas a elegir) con publicaciones, interacciones, impresiones/vistas, crecimiento de seguidores, la mejor y la peor publicación, y una frase generada a partir de esos mismos datos guardados (nunca un texto inventado ni al azar). Un campo que la API de esa plataforma no expone se muestra siempre como **"No disponible"**, nunca como 0, para no confundir "no hay datos" con "no pasó nada".

**Desconectar una plataforma** pide confirmación, intenta revocar el acceso en la plataforma cuando esa red lo permite, y borra las credenciales guardadas — pero **conserva todo el historial de métricas** (publicaciones, estadísticas, resúmenes) salvo que se marque explícitamente la opción de borrar también el histórico al desconectar.

**Lo que queda registrado en la Bitácora:** conectar, renovar, sincronizar, fallar una sincronización, requerir reconexión y desconectar — nunca las credenciales en sí.

### Qué significa cada número por plataforma

La sincronización usa, para cada plataforma, los campos que su API pública realmente expone — no son los mismos conceptos exactos en todas:

| Plataforma | Seguidores | Por publicación | Vistas / impresiones |
|---|---|---|---|
| Facebook | Total de "me gusta" de la página | Me gusta, comentarios y compartidos de cada publicación | Impresiones de cada publicación, cuando Meta las expone; si no, "No disponible" |
| Instagram | Seguidores de la cuenta | Me gusta y comentarios de cada publicación | "No disponible" (este alcance de la API no expone impresiones por publicación) |
| TikTok | Seguidores de la cuenta | Me gusta, comentarios y compartidos de cada video | Vistas de cada video; impresiones a nivel de cuenta no disponibles con esta API |
| YouTube | Suscriptores del canal (si el propio canal no los oculta) | Me gusta y comentarios de cada video | Vistas de cada video; impresiones no disponibles con esta API |

### Por qué X (antes Twitter) no está en este módulo

Esta entrega rehízo el módulo de redes sociales para usar el inicio de sesión real (OAuth) de Facebook, Instagram, TikTok y YouTube; X no se incluyó en esta nueva versión. El módulo anterior sí tenía un cliente de X con un token pegado a mano, y se retiró junto con todo el sistema de pegar credenciales. Si más adelante se necesita, se agrega como un adaptador nuevo siguiendo el mismo patrón que los otros cuatro (interfaz `SocialProvider` en `nexus-control-api/app/services/social/providers/`), sin tocar el resto del módulo.

### Límites honestos que hay que conocer

- **Meta (Facebook/Instagram) y TikTok exigen pasar por la revisión de su app** ("App Review") para que cualquier cliente, y no solo las cuentas de prueba del desarrollador, pueda conectar su cuenta. Mientras eso no se complete, solo las cuentas agregadas como administrador/desarrollador/tester en el panel de esa red pueden conectarse; `CONFIGURAR_REDES_SOCIALES.md` explica ese trámite.
- **YouTube/Google, mientras la app no esté verificada, deja de renovar el acceso cada 7 días**, obligando a reconectar el canal cada semana. `CONFIGURAR_REDES_SOCIALES.md` explica cómo pasar la app a producción para quitar ese límite.
- Este flujo de OAuth no se pudo probar en vivo contra Facebook, TikTok ni Google durante el desarrollo, porque este entorno no tiene salida de red hacia esos servidores; sí se probó a fondo con pruebas automatizadas que verifican la lógica completa (estado, cifrado, renovación, reintentos, sincronización) simulando las respuestas de cada API. La primera conexión real que hagas, con tus propias credenciales, es la verdadera prueba del flujo completo; si algo no calza, el "Último error" de la tarjeta trae el mensaje exacto que devolvió la plataforma.

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
| `nexus-control-api/` | API Flask: fábrica de la app, extensiones, seguridad HTTP, límite de peticiones, CORS, Socket.IO, bitácora, migraciones Alembic, Docker (API + PostgreSQL + Redis), súper admin, login con JWT y 2FA, Administradores, Bitácora, Equipos (PC y Android) y Categorías, los endpoints para el agente (enrolamiento, inventario, señal de vida, catálogo de apps instaladas), la matriz de control de aplicaciones (`/api/equipos/<id>/aplicaciones`, `/api/equipos/<id>/uso`) y sus endpoints para el agente (`/api/agente/politicas`, `/api/agente/uso`, `/api/agente/apps-instaladas`), el resumen del Inicio (`/api/dashboard/resumen`), las métricas manuales de redes sociales (`/api/metricas-sociales`), el módulo de **Redes sociales** con OAuth 2.0 real (`/api/redes-sociales`: conectar, callback, sincronizar, desconectar, salud, estado del sistema y resumen de actividad), cifrado de tokens con AES-256-GCM, los adaptadores de Facebook/Instagram/TikTok/YouTube y el sincronizador en segundo plano con reintentos, y los reportes en PDF/CSV/Excel (`/api/reportes/general`, `/api/reportes/uso`, `/api/reportes/auditoria`). |
| `nexus-control-frontend/` | React + Vite + Tailwind. Login, 2FA, layout con menú lateral y búsqueda `⌘K`, Mi perfil, Administradores, Bitácora, Equipos (tarjetas, filtros, alta con selector de tipo PC/Android y código de enrolamiento — el hostname/IP/sistema operativo ya no se escriben a mano —, y la pestaña "Aplicaciones" con la matriz de control, el catálogo de apps instaladas en Android y el uso por aplicación), Inicio (indicadores en vivo y resumen de redes sociales, manual o automático), **Redes sociales** (conectar Facebook/Instagram/TikTok/YouTube con OAuth real, panel de administración, estado del sistema y resumen de actividad) y Reportes (descarga de los tres reportes en PDF/CSV/Excel), todo reflejado en vivo cuando un agente real se conecta o reporta uso. |
| `nexus-control-agent/` | El programa en Python que se instala en cada PC: se enrola con el código, manda su inventario y una señal de vida cada 30 segundos, aplica la matriz de control (bloqueo y límites de tiempo) y reporta el uso real de cada aplicación. Tiene su propio `INICIAR_AGENTE_EN_PC.bat` y README. |
| `nexus-control-android/` | Proyecto de Android Studio (Kotlin) que se instala en celulares y tablets: se enrola con el código, sube su inventario y el catálogo de apps instaladas, y aplica la matriz de control con una pantalla de bloqueo propia de Nexus Obsidian. Tiene su propio README, un `INSTALAR_APK_EN_PC.bat` y un flujo de GitHub Actions que lo compila y le corre las pruebas. |
| `INICIAR_EN_PC.bat` y `DETENER_EN_PC.bat` | Arrancan y apagan el panel y el servidor con doble clic. |
| `CONFIGURAR_REDES_SOCIALES.md` | Guía paso a paso, sin dar por hecho que sabes de desarrollo, para dar de alta Facebook, Instagram, TikTok y YouTube en sus paneles de desarrolladores y conectar el módulo de Redes sociales. |
| `scripts/` | Script de PowerShell que crea el `.env` con claves aleatorias (incluye la clave de cifrado de los tokens de redes sociales). |
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

Debes ver `256 passed` (incluye las pruebas del nuevo módulo de Redes sociales con OAuth; una de las pruebas de 2FA espera hasta 30 segundos a propósito, por eso la corrida completa toma unos minutos).

Frontend:

```
npm test
```

Debes ver `52 passed`.

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
