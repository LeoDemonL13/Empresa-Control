# Configurar las redes sociales (Facebook, Instagram, TikTok, YouTube)

Esta guía explica, paso a paso y sin dar por hecho que sabes de desarrollo, cómo dar de alta
cada red social para que Nexus Obsidian Control pueda conectarse a ella con el inicio de sesión
real de la plataforma (OAuth) y sincronizar sus métricas automáticamente.

No necesitas tocar código. Solo necesitas:

1. Crear una "aplicación" dentro del panel de desarrolladores de cada red social (es gratis).
2. Copiar unos identificadores (parecen códigos largos de letras y números) a tu archivo `.env`.
3. Guardar y reiniciar el servidor.

Repite la sección correspondiente por cada red que quieras conectar. Puedes dejar sin configurar
las que no uses: el sistema seguirá funcionando con las demás, y la tarjeta de la red sin
configurar mostrará un aviso en vez de un botón de "Conectar".

---

## Antes de empezar: ¿dónde se guardan estos datos?

Todas las variables que vas a copiar se guardan en el archivo `nexus-control-api/.env`
(si usaste `INICIAR_EN_PC.bat`, ese archivo ya existe y se generó solo la primera vez que
abriste el programa). Ábrelo con el Bloc de notas, busca la variable por su nombre, y escribe
el valor después del signo `=`. Ejemplo:

```
META_APP_ID=1234567890123456
```

Después de editar el archivo, cierra el servidor (`DETENER_EN_PC.bat`) y vuelve a abrirlo
(`INICIAR_EN_PC.bat`) para que tome los cambios.

### La URL de redirección

Cada red social te va a pedir una "URL de redirección" (o "Redirect URI"). Es la dirección a la
que la red social devuelve al usuario después de iniciar sesión. En este proyecto, el patrón es
siempre:

```
<dirección del servidor>/api/redes-sociales/callback/<plataforma>
```

- Si estás probando en tu propia computadora (lo normal con `INICIAR_EN_PC.bat`):
  `http://localhost:5001/api/redes-sociales/callback/facebook` (o `instagram`, `tiktok`,
  `youtube` según la red).
- Si el sistema ya está publicado en un dominio real (por ejemplo
  `https://control.miempresa.com`):
  `https://control.miempresa.com/api/redes-sociales/callback/facebook`, y así para cada red.

Usa exactamente esa misma URL en dos lugares: en el panel de la red social (donde te la pide) y
en la variable `..._REDIRECT_URI` correspondiente en `.env`. Si no coinciden letra por letra
(incluyendo `http` vs `https`), la red social rechazará la conexión.

Si más adelante cambias de dominio, solo tienes que añadir la nueva URL en el panel de la red
social y actualizar la variable en `.env`; el código no necesita cambios.

---

## 1. Facebook e Instagram (Meta)

Facebook e Instagram comparten la misma aplicación de Meta, por eso usan las mismas tres
variables (`META_APP_ID`, `META_APP_SECRET`, `META_REDIRECT_URI`) aunque se conecten por
separado desde el panel.

**Requisito para Instagram:** la cuenta de Instagram debe ser una cuenta "Business" o "Creator"
(no personal) y debe estar vinculada a una página de Facebook. Meta no permite conectar cuentas
personales de Instagram por API.

### Pasos

1. Entra a [developers.facebook.com](https://developers.facebook.com/) e inicia sesión con la
   cuenta de Facebook de la empresa (no una personal, si puedes evitarlo).
2. Arriba a la derecha, "Mis aplicaciones" → "Crear aplicación".
3. Elige el tipo "Empresa" y dale un nombre (por ejemplo, "Nexus Obsidian Control").
4. Dentro de la aplicación, en el panel lateral, busca "Agregar producto" y añade:
   - **Inicio de sesión con Facebook** (Facebook Login): habilita el flujo de autorización.
   - **API Graph de Instagram** (Instagram Graph API): habilita leer datos de Instagram.
5. Dentro de "Inicio de sesión con Facebook" → "Configuración", en el campo
   "URI de redirección de OAuth válidas" pega la URL de redirección (ver sección anterior,
   usando `facebook` o `instagram` según cuál conectes; si vas a usar ambas, agrega las dos
   URLs, una por línea).
6. Ve a "Configuración" → "Básica" (panel principal de la app). Ahí verás:
   - **ID de la aplicación**: cópialo en `META_APP_ID`.
   - **Clave secreta**: haz clic en "Mostrar", confírmalo con tu contraseña, y cópialo en
     `META_APP_SECRET`. Trátalo como una contraseña: nunca lo compartas ni lo subas a internet.
7. En `META_REDIRECT_URI` escribe la misma URL que pusiste en el paso 5.
8. Guarda el archivo `.env` y reinicia el servidor.

### Permisos que pide el sistema

- `pages_show_list`, `pages_read_engagement`, `pages_read_user_content`, `read_insights`,
  `business_management` (para Facebook).
- `instagram_basic`, `instagram_manage_insights` (para Instagram), más los permisos de
  Facebook anteriores (porque Instagram se consulta a través de la página vinculada).

### De pruebas a producción

Mientras tu app esté en "Modo de desarrollo" (el estado por defecto), **solo** las cuentas que
agregues como "Administrador", "Desarrollador" o "Tester" en "Funciones de la aplicación" →
"Funciones" podrán conectar sus páginas. Para que cualquier cliente pueda conectar su propia
página, Meta exige pasar la app a **Modo activo** (En vivo) y, para los permisos avanzados
(`pages_read_engagement`, `instagram_manage_insights`, `read_insights`, etc.), completar la
**Revisión de la app** (App Review): un formulario donde explicas para qué usas cada permiso,
y en algunos casos grabas un video de pantalla mostrando el flujo de conexión. Meta puede tardar
varios días en revisarlo. Hasta que se apruebe, el sistema funciona con normalidad para las
cuentas de prueba que hayas dado de alta.

---

## 2. TikTok

### Pasos

1. Entra a [developers.tiktok.com](https://developers.tiktok.com/) e inicia sesión (o crea una
   cuenta) con la cuenta de TikTok de la empresa.
2. "Manage apps" → "Create an app".
3. Dale un nombre y una categoría a la app.
4. En "Add products", agrega **Login Kit** (para el inicio de sesión) y **Display API** (para
   leer estadísticas y videos).
5. En la configuración del producto **Login Kit**, en "Redirect URI" pega la URL de
   redirección (sección "Antes de empezar", usando `tiktok`).
6. En el resumen de la app verás:
   - **Client Key**: cópialo en `TIKTOK_CLIENT_KEY`.
   - **Client Secret**: cópialo en `TIKTOK_CLIENT_SECRET` (trátalo como una contraseña).
7. En `TIKTOK_REDIRECT_URI` escribe la misma URL del paso 5.
8. Guarda `.env` y reinicia el servidor.

### Permisos que pide el sistema

`user.info.basic`, `user.info.stats`, `video.list`.

### De pruebas a producción

Una app nueva de TikTok empieza en estado de **auditoría/sandbox**: solo los usuarios que
agregues como colaboradores de la app en el panel de desarrolladores pueden conectar su cuenta.
Para que cualquier persona pueda conectar la suya, TikTok exige enviar la app a **revisión**
desde "App review" en el panel, donde debes describir el uso de cada permiso (especialmente
`video.list`, que requiere justificar para qué se usan los datos de los videos). La revisión la
hace TikTok manualmente y puede tardar varios días.

**Importante sobre el refresh token:** cada vez que el sistema renueva el acceso con TikTok,
TikTok entrega un `refresh_token` nuevo y da de baja el anterior. El sistema ya hace esto de
forma automática (siempre guarda el más reciente), así que no tienes que hacer nada, pero si
alguna vez ves que una conexión de TikTok pide reconectarse sin motivo aparente, puede ser que
el proceso se haya interrumpido justo durante una renovación; basta con volver a pulsar
"Conectar con TikTok".

---

## 3. YouTube (Google)

### Pasos

1. Entra a [console.cloud.google.com](https://console.cloud.google.com/) con una cuenta de
   Google (idealmente una de la empresa, no personal).
2. Arriba, el selector de proyectos → "Proyecto nuevo". Dale un nombre (por ejemplo,
   "Nexus Obsidian Control") y créalo.
3. Con el proyecto seleccionado, ve a "APIs y servicios" → "Biblioteca", busca
   **YouTube Data API v3** y haz clic en "Habilitar".
4. Ve a "APIs y servicios" → "Pantalla de consentimiento de OAuth":
   - Tipo de usuario: "Externo" (a menos que toda tu organización use Google Workspace, en
     cuyo caso puedes elegir "Interno").
   - Completa el nombre de la app y un correo de contacto.
   - En "Scopes" (permisos), agrega `.../auth/youtube.readonly`.
   - En "Usuarios de prueba" (si elegiste "Externo"), agrega las cuentas de Google de las
     personas que van a conectar su canal mientras la app no esté verificada (ver más abajo).
5. Ve a "APIs y servicios" → "Credenciales" → "Crear credenciales" → "ID de cliente de OAuth".
   - Tipo de aplicación: "Aplicación web".
   - En "URI de redirección autorizados", pega la URL de redirección (sección "Antes de
     empezar", usando `youtube`).
6. Al crear las credenciales, Google te muestra:
   - **ID de cliente**: cópialo en `GOOGLE_CLIENT_ID`.
   - **Secreto del cliente**: cópialo en `GOOGLE_CLIENT_SECRET`.
7. En `GOOGLE_REDIRECT_URI` escribe la misma URL del paso 5.
8. Guarda `.env` y reinicia el servidor.

### Permisos que pide el sistema

`https://www.googleapis.com/auth/youtube.readonly` (solo lectura: estadísticas del canal y de
los videos; el sistema nunca sube, edita ni borra nada en YouTube).

### El límite de 7 días en modo de prueba (muy importante)

Mientras tu app de Google esté **sin verificar** (lo normal al principio), Google limita la
sesión a cuentas que agregaste como "Usuarios de prueba" y, en algunos casos, **el acceso de
renovación (`refresh_token`) deja de funcionar pasados 7 días**, obligando a reconectar el
canal. Esto es una limitación impuesta por Google, no un error del sistema.

Para quitar ese límite necesitas **verificar la app** desde la pantalla de consentimiento de
OAuth ("Publicar aplicación" → pasar de "Prueba" a "Producción"). Si solo usas el scope
`youtube.readonly` sobre tu propio canal, Google normalmente no exige una revisión manual
extensa para pasar a producción, pero sí puede pedir verificación de dominio y, si en el futuro
se agregan permisos más sensibles, una revisión de seguridad (CASA). Mientras no verifiques la
app, el sistema sigue funcionando para los canales que agregaste como usuarios de prueba, solo
que tendrás que reconectar cada ~7 días.

---

## ¿Qué pasa si no configuro alguna red?

Nada se rompe. La tarjeta de esa red en el panel mostrará "no tiene configuradas sus
credenciales de aplicación" en lugar del botón para conectar, y el resto de las redes sigue
funcionando con normalidad. Puedes volver a esta guía en cualquier momento.

## ¿Qué pasa si cambio de dominio o de servidor?

Actualiza la variable `..._REDIRECT_URI` que corresponda y agrega la nueva URL en el panel de
desarrolladores de esa red (sin borrar la anterior si todavía la usas, por ejemplo para
pruebas locales). No hay que tocar código ni volver a autorizar las cuentas que ya estén
conectadas, salvo que la red social lo pida explícitamente.
