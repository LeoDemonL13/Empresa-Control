# Agente Android de Nexus Obsidian Control

App para Android que hace, en celulares y tablets de la empresa, lo mismo que el agente de Windows hace en las PC: se enrola con un código, reporta el equipo al panel y aplica la matriz de control de aplicaciones (bloquear una app o limitarle los minutos de uso al día).

Android no permite cerrar otra app a la fuerza como sí se puede en Windows (eso exigiría permisos de administrador del dispositivo o una app "device owner" instalada por MDM). Por eso el bloqueo funciona distinto, pero con el mismo resultado práctico: en cuanto la persona abre una app bloqueada o agotada, el agente le pone encima una pantalla con la marca de Nexus Obsidian que le explica por qué no puede usarla, y a los pocos segundos la regresa sola a la pantalla de inicio (o ella puede tocar el botón para volver antes).

No usa permisos de "administrador del dispositivo" ni requiere rootear el celular ni instalar ningún MDM: solo pide activar un Servicio de Accesibilidad (así es como detecta qué app está al frente) y, opcionalmente, permitir que la app funcione sin restricciones de batería.

## Aviso importante sobre esta entrega

Este proyecto se escribió en un entorno en la nube sin SDK de Android y sin acceso a los servidores de Google (`dl.google.com`, `maven.google.com`) ni a Maven Central, así que **no fue posible compilarlo ni ejecutarlo aquí**, a diferencia del resto de Nexus Obsidian Control (API, panel y agente de Windows), que sí se probó en vivo end-to-end.

Para compensarlo:

- Todo el contrato con el servidor (`/api/agente/enrolar`, `/api/agente/inventario`, `/api/agente/politicas`, `/api/agente/uso`, `/api/agente/apps-instaladas`) se verificó primero en vivo contra el servidor real, simulando con `curl` todo el ciclo de vida de un agente Android, antes de escribir una sola línea de Kotlin.
- La lógica de negocio que no depende de Android (cuándo bloquear una app, y cómo se calcula qué enviar al servidor sin duplicar minutos) se extrajo a clases Kotlin puras (`Politica.kt`, `CalculoUso.kt`) y se verificó de dos formas: ejecutándola de verdad con el compilador de Kotlin fuera de este proyecto, y con pruebas JUnit reales incluidas en `app/src/test/`.
- Se agregó un flujo de **GitHub Actions** (`.github/workflows/android-build.yml`) que compila el proyecto completo y corre esas pruebas automáticamente en cuanto subas esta carpeta a GitHub, con runners que sí tienen acceso a los servidores de Google. Es la forma de obtener una verificación real y automática sin depender de este entorno.
- Recomendamos firmemente hacer una primera prueba completa en un celular real (ver "Probarlo paso a paso" más abajo) antes de instalarlo en los equipos de la empresa.

## Qué hace exactamente

- **Enrolamiento:** igual que el agente de Windows, pide la dirección del servidor y el código de enrolamiento de 11 caracteres que se genera en el panel (Equipos → Agregar equipo, con tipo "Celular o tablet Android").
- **Inventario:** manda modelo de equipo, IP y versión de Android a `/api/agente/inventario`, lo mismo que usa el panel para mostrarlo "En línea".
- **Catálogo de apps instaladas:** sube la lista de apps visibles del celular (nombre de paquete y nombre que ve la persona) para que, al configurar la matriz de control desde el panel, el administrador pueda elegir la app de una lista en vez de escribir el nombre del paquete a mano.
- **Políticas:** descarga la matriz de control configurada para ese equipo (permitida/bloqueada, sin límite/con límite y los minutos) y la vuelve a descargar cada minuto, además de cada 15 minutos por una tarea de respaldo que sigue funcionando aunque el teléfono se reinicie.
- **Detección de la app en primer plano:** un Servicio de Accesibilidad (sin leer el contenido de las pantallas, solo qué paquete está al frente) vigila los cambios de app en tiempo real.
- **Bloqueo:** si la app al frente está bloqueada, o si ya se le acabó su límite de minutos del día, aparece la pantalla de bloqueo de Nexus Obsidian explicando el motivo y, a los 6 segundos (o antes, si la persona toca el botón), regresa sola al inicio.
- **Uso real:** acumula en el propio celular los segundos de uso de cada app, igual que el agente de Windows, y los reporta al servidor por minuto solo lo nuevo desde el último envío (nunca el total acumulado del día, para no inflar los números del panel).

## Qué se necesita para compilarlo

- **Android Studio** (gratis, de Google) en una PC con internet normal — no hace falta ninguna cuenta de pago ni la Play Store.
- Un celular o tablet Android **8.0 o superior** para probarlo (minSdk 26).

## Compilarlo con Android Studio

1. Abre Android Studio → **Open** → selecciona la carpeta `nexus-control-android`.
2. Espera a que termine de sincronizar (la primera vez descarga el Gradle, el SDK y las librerías; puede tardar varios minutos según tu internet).
3. Conecta el celular por USB con la **depuración USB** activada (Ajustes → Acerca del teléfono → toca 7 veces "Número de compilación" para activar "Opciones de desarrollador", luego Ajustes → Opciones de desarrollador → Depuración USB), o usa un emulador creado desde Android Studio (Device Manager).
4. Presiona el botón verde ▶ (Run 'app') en Android Studio. Se compila, se instala y se abre sola en el celular.

Si prefieres la línea de comandos (con el celular ya conectado):

```
gradlew.bat installDebug
```

(en Mac/Linux sería `./gradlew installDebug`).

## Generar el APK para repartirlo a varios equipos

En Android Studio: **Build → Build Bundle(s) / APK(s) → Build APK(s)**. El archivo queda en:

```
app\build\outputs\apk\debug\app-debug.apk
```

Para instalarlo en otro celular sin pasar por Android Studio, copia ese `.apk` a la PC que lo vaya a repartir y usa **`INSTALAR_APK_EN_PC.bat`** (pide tener `adb` en el PATH; viene con Android Studio en `%LOCALAPPDATA%\Android\Sdk\platform-tools`), o simplemente copia el `.apk` al celular y ábrelo ahí (hay que permitir "instalar apps de orígenes desconocidos" la primera vez).

## Probarlo paso a paso

1. Con el servidor (`nexus-control-api`) corriendo y alcanzable desde la red del celular (usa la IP de la PC del servidor, no `localhost`, salvo que pruebes en un emulador en la misma PC), crea un equipo nuevo en el panel con tipo **"Celular o tablet Android"** y copia su código de enrolamiento.
2. Instala y abre la app en el celular. Escribe la dirección del servidor (ejemplo `http://192.168.1.50:5001`) y el código, y toca "Enrolar este dispositivo".
3. En el panel, el equipo debe pasar a "En línea" en menos de un minuto.
4. En la app, toca "Activar supervisión": te manda a Ajustes → Accesibilidad. Busca "Nexus Obsidian Control" en la lista y activa el interruptor. Acepta la advertencia de Android (es el aviso genérico que sale para cualquier app con este tipo de servicio).
5. De vuelta en la app, también conviene tocar "Permitir funcionamiento en segundo plano" para que Android no lo pause por ahorro de batería.
6. En el panel, abre ese equipo con "Ver" → pestaña "Aplicaciones" y agrega alguna app instalada en el celular (si ya sincronizó su inventario, aparece en una lista para elegir en vez de escribir el nombre del paquete). Bloquéala.
7. En el celular, abre esa app: en unos segundos debe aparecer la pantalla roja de bloqueo y regresar sola al inicio.
8. Prueba también "Con límite" con 1 minuto, usa otra app permitida durante más de un minuto, y confirma que también se bloquea al pasar el minuto y que el tiempo usado se ve reflejado en el panel.

## Problemas comunes

**La app en el panel no pasa a "En línea".** Revisa que el celular y el servidor estén en la misma red y que la dirección tenga el puerto (`:5001`). Si el servidor usa HTTPS con un certificado propio, esta primera versión solo contempla HTTP plano en la red local (por simplicidad, igual que el agente de Windows en su configuración por defecto).

**La pantalla de bloqueo no aparece.** Lo más común es que el Servicio de Accesibilidad no esté activado (revisa el estado en la propia app) o que Android haya puesto la app a dormir por ahorro de batería (usa el botón de "Permitir funcionamiento en segundo plano"). En celulares Xiaomi, Huawei, Oppo/Realme y similares, además puede haber un ajuste propio del fabricante como "Inicio automático" o "Ahorro de batería inteligente" que hay que desactivar para esta app a mano; varía según la marca y el proveedor.

**Quiero quitar el agente de un celular.** Abre la app, toca "Desenrolar este dispositivo", y desinstala la app o desactiva el Servicio de Accesibilidad desde Ajustes si ya no la vas a volver a usar.

## Ejecutar las pruebas automatizadas

Con el proyecto abierto en Android Studio: clic derecho sobre `app/src/test` → **Run Tests**. Por línea de comandos:

```
gradlew.bat test
```

Debes ver los resultados de `PoliticaTest` (las reglas de bloqueo) y `CalculoUsoTest` (que cada sincronización solo envía los minutos nuevos, nunca el total del día de nuevo) en verde.

## Verificación automática con GitHub Actions

Si subes esta carpeta (o todo `nexus-control/`) a un repositorio de GitHub, el flujo en `.github/workflows/android-build.yml` compila el proyecto y corre las pruebas solo. Para verlo:

1. Sube los cambios a GitHub (`git push`).
2. Entra a la pestaña **Actions** del repositorio.
3. Busca la ejecución de "Android build"; en verde significa que compiló y las pruebas pasaron. El `.apk` de depuración queda descargable ahí mismo, en "Artifacts".

Este flujo asume que la carpeta `nexus-control-android` está justo en la raíz del repositorio (junto a `.github/`). Si en tu repositorio queda en otra ruta, mueve la carpeta `.github` a la raíz real del repositorio y ajusta la línea `working-directory` y los `paths` del archivo `android-build.yml` a esa ruta.

## Estructura

| Carpeta | Contenido |
|---|---|
| `app/src/main/java/.../data/` | Credenciales guardadas, estado local de uso (`AlmacenEstado`), cliente HTTP (`ApiCliente`), la regla de bloqueo (`Politica`) y el cálculo de qué enviar en cada sincronización (`CalculoUso`). |
| `app/src/main/java/.../servicio/` | El Servicio de Accesibilidad que detecta la app al frente y dispara el bloqueo, la tarea periódica de respaldo (WorkManager) y el receptor de arranque del celular. |
| `app/src/main/java/.../ui/` | La pantalla de enrolamiento/estado y la pantalla de bloqueo. |
| `app/src/test/` | Pruebas JUnit de la lógica de bloqueo y de cálculo de uso. |
| `.github/workflows/` | Compilación y pruebas automáticas en GitHub Actions. |
