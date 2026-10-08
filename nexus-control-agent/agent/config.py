import os

ARCHIVO_CREDENCIALES = os.environ.get(
    'NEXUS_CREDENCIALES_PATH',
    os.path.join(os.environ.get('PROGRAMDATA', '.'), 'NexusObsidianControl', 'device.json'),
)
ARCHIVO_LOG = os.environ.get(
    'NEXUS_LOG_PATH',
    os.path.join(os.environ.get('PROGRAMDATA', '.'), 'NexusObsidianControl', 'agente.log'),
)
AGENTE_VERSION = '0.1.0'
INTERVALO_HEARTBEAT_SEGUNDOS = int(os.environ.get('NEXUS_INTERVALO_HEARTBEAT', '30'))
INTERVALO_MONITOREO_SEGUNDOS = int(os.environ.get('NEXUS_INTERVALO_MONITOREO', '15'))
INTERVALO_SINCRONIA_SEGUNDOS = int(os.environ.get('NEXUS_INTERVALO_SINCRONIA', '60'))
URL_POR_DEFECTO = 'http://localhost:5001'
