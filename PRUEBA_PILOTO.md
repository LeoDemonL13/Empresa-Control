# Prueba piloto: 2 PC y 2 celulares

Hazla antes de instalar nada en los 50 equipos. Necesitas el servidor funcionando (en tu PC con `INICIAR_EN_PC.bat` o en el Mini PC), 2 PC con Windows y 2 celulares Android que puedan alcanzar la dirección del servidor.

## 0. Preparar el servidor

1. Entra al panel como súper admin.
2. Crea una categoría (por ejemplo "Piloto").
3. Si el servidor es el Mini PC con dominio, la dirección es `https://tu-dominio`. Si es tu PC en red local, es `http://IP_DE_TU_PC:5001`. Los celulares y las PC deben poder abrir esa dirección en su navegador.

## 1. PC con Windows

1. En GitHub: **Actions → agente-windows**, última ejecución en verde, descarga el artefacto `nexus-agente-windows`. Descomprímelo en la PC.
2. Panel → **Equipos → Agregar equipo** (tipo PC) → copia el código.
3. Abre `INSTALAR_AGENTE_WINDOWS.bat`, acepta el permiso de administrador, escribe la dirección y el código.
4. **Esperado:** en menos de un minuto el equipo aparece "En línea" y se ven hostname, IP y sistema operativo.
5. **Reinicio:** reinicia la PC sin abrir nada. **Esperado:** al volver a encender, el equipo vuelve a "En línea" solo, antes de iniciar sesión.
6. **Bloqueo:** en el panel, pestaña Aplicaciones del equipo, agrega `notepad.exe` y márcalo "Bloqueada". Abre el Bloc de notas. **Esperado:** se cierra solo en unos segundos.
7. **Límite:** agrega `calc.exe` con límite de 1 minuto. Ábrela más de un minuto. **Esperado:** se cierra y el panel muestra el uso.
8. **Usuario estándar:** con una cuenta sin permisos de administrador abre el Administrador de tareas e intenta finalizar `nexus-agente.exe`. **Esperado:** no puede. Intenta abrir `C:\ProgramData\NexusObsidianControl`. **Esperado:** acceso denegado.
9. **Servidor reiniciado:** reinicia la API (`nexus-ctl reiniciar` en el Mini PC o reinicia el contenedor `api`). **Esperado:** el equipo pasa a "Fuera de línea" y vuelve a "En línea" solo, sin tocar la PC.
10. **Desinstalar:** `DESINSTALAR_AGENTE_WINDOWS.bat`. **Esperado:** el equipo pasa a "Fuera de línea" y no queda tarea ni carpeta.

Si algo falla, el registro está en `C:\ProgramData\NexusObsidianControl\agente.log`.

## 2. Celulares Android

1. En GitHub: **Actions → android-build**, última ejecución en verde, descarga el artefacto `nexus-obsidian-control-android-debug` (contiene `app-debug.apk`).
2. Cópialo al celular (cable, WhatsApp a ti mismo, o `INSTALAR_APK_EN_PC.bat` con depuración USB) y ábrelo; permite "instalar apps de orígenes desconocidos" cuando lo pida.
3. Panel → **Equipos → Agregar equipo** (tipo celular o tablet) → copia el código.
4. Abre la app, escribe la dirección del servidor y el código.
5. **Esperado:** el equipo aparece "En línea" en el panel con el modelo y la versión de Android.
6. Toca "Activar supervisión" y activa el servicio en Ajustes → Accesibilidad. Si Android 13+ lo impide, usa "Permitir ajustes restringidos" (ver `nexus-control-android/README.md`). Toca también "Permitir funcionamiento en segundo plano".
7. En el panel, pestaña Aplicaciones, elige una app de la lista (por ejemplo Calculadora) y márcala "Bloqueada". **Esperado:** al abrirla en el celular aparece la pantalla de bloqueo y regresa sola al inicio.
8. Prueba "Con límite" de 1 minuto con otra app y úsala más de un minuto. **Esperado:** se bloquea y el panel muestra el uso.
9. Bloquea la pantalla del celular 10 minutos y desbloquéalo. Reinicia el celular. **Esperado:** el equipo sigue reportando y bloqueando sin abrir la app a mano. Si no lo hace (sobre todo en Xiaomi, Huawei, Oppo, Realme), revisa "Inicio automático" y "Ahorro de batería" de esa marca.
10. Anota el modelo y la versión de Android de cada celular y qué falló: así se corrige con datos reales.

## 3. Qué reportar

Para cada paso que falle: número de paso, qué viste en pantalla y, en Windows, las últimas líneas de `agente.log`. Con eso se corrige.
