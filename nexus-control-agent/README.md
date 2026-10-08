# Agente de Nexus Obsidian Control

Programa que se instala en cada equipo para que aparezca en el panel. Se enrola, manda su inventario básico (hostname, IP, MAC, sistema operativo) y una señal de vida cada 30 segundos para que el panel sepa que está en línea.

Desde la **Fase 4**, además aplica la matriz de control de aplicaciones que se configura desde el panel:

- Cada pocos segundos revisa qué programas están corriendo en el equipo y los compara contra las políticas (Permitida/Bloqueada, Sin límite/Con límite).
- Si una aplicación está **Bloqueada**, o si ya alcanzó su **límite de minutos diario**, el agente cierra el proceso automáticamente.
- El tiempo de uso de cada aplicación se acumula localmente y se envía al panel cada minuto, para que se vea en la pestaña "Aplicaciones" del equipo.
- Cuando un administrador cambia una política desde el panel, el agente la recibe al instante (por WebSocket) y la aplica sin esperar al siguiente ciclo.
- Si se pierde la conexión con el servidor, el agente sigue aplicando las últimas políticas que conoce y sigue acumulando el uso localmente; en cuanto vuelve la conexión, sincroniza todo.

## Instalación en las PC de la empresa (recomendada)

Para producción no uses `INICIAR_AGENTE_EN_PC.bat`: necesita Python, abre una ventana y se detiene al cerrarla. Usa el paquete ya compilado:

1. En GitHub, pestaña **Actions → agente-windows**, abre la última ejecución en verde y descarga el artefacto **nexus-agente-windows** (un .zip). Descomprímelo en la PC (o en una USB para repartirlo).
2. En el panel: **Equipos → Agregar equipo**, tipo PC, y copia el código (dura 30 minutos).
3. Doble clic en **`INSTALAR_AGENTE_WINDOWS.bat`**, acepta el permiso de administrador y escribe la dirección del servidor (por ejemplo `https://nexus.miempresa.com`) y el código. También acepta ambos como argumentos: `INSTALAR_AGENTE_WINDOWS.bat https://nexus.miempresa.com CODIGO`.
4. En menos de un minuto el equipo debe aparecer "En línea". No hace falta Python ni dejar nada abierto.

Qué deja instalado:

- `C:\Program Files\NexusObsidianControl\nexus-agente.exe`, ejecutado por una tarea programada **al encender el equipo**, como SYSTEM, sin ventana, reiniciándose sola cada minuto si se cae.
- Los datos (credenciales, estado de uso y registro `agente.log`) en `C:\ProgramData\NexusObsidianControl`, accesibles solo para SYSTEM y administradores. Un usuario estándar no puede ver la clave, editar el uso acumulado ni detener el agente; un administrador local sí puede.
- Para quitarlo: **`DESINSTALAR_AGENTE_WINDOWS.bat`** (después elimina el equipo del panel).

Instalarlo otra vez sobre una PC ya enrolada actualiza el programa y conserva sus credenciales.

El agente cuenta como "tiempo de uso" el tiempo que el programa está abierto como proceso, no el tiempo con la ventana al frente.

Modo de línea de comandos: `nexus-agente.exe --enrolar URL CODIGO` (enrola y termina) y `nexus-agente.exe --servicio` (desatendido, sin preguntas, con registro en archivo).

## Requisitos para el modo de desarrollo (.bat con Python)

- Python 3.11 o superior en el equipo donde se instale.
- Que el panel y el servidor (`nexus-control-api`) ya estén corriendo y sean alcanzables desde este equipo.

## Uso

Haz doble clic en **`INICIAR_AGENTE_EN_PC.bat`**.

La primera vez te pide dos cosas:

1. **Dirección del servidor.** Si el agente corre en la misma PC que el servidor, deja el valor por defecto (`http://localhost:5001`) con Enter. Si corre en otra PC de la red, escribe la IP de la PC donde está el servidor, por ejemplo `http://192.168.1.50:5001`.
2. **Código de enrolamiento.** Lo generas en el panel, en **Equipos → Agregar equipo** (o, si el equipo ya existe, abriéndolo con "Ver" y usando "Generar código"). El código se ve una sola vez y vence en 30 minutos.

Con eso el agente queda enrolado y guarda sus credenciales en:

```
%PROGRAMDATA%\NexusObsidianControl\device.json
```

Las siguientes veces que abras `INICIAR_AGENTE_EN_PC.bat`, arranca directo, sin preguntar nada, y en el panel el equipo debe pasar a "En línea" en segundos.

## Volver a enrolar un equipo

Si borras el equipo del panel y lo vuelves a dar de alta, o si quieres asignarle un código nuevo, borra el archivo `device.json` de la ruta de arriba y vuelve a abrir `INICIAR_AGENTE_EN_PC.bat`: te va a pedir un código nuevo.

## Ejecutar las pruebas

```
INICIAR_AGENTE_EN_PC.bat
```

prepara el entorno; para correr las pruebas automatizadas con ese mismo entorno ya preparado:

```
.venv\Scripts\activate
pip install pytest
pytest -q
```

Debes ver `43 passed`.
