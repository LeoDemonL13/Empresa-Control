from unittest.mock import patch

from agent.inventario import _mac_local, recolectar


def test_recolectar_incluye_los_campos_esperados():
    datos = recolectar()
    assert set(datos) == {'hostname', 'ip', 'mac', 'sistema_operativo'}
    assert datos['hostname']


def test_mac_local_none_si_uuid_es_aleatorio():
    with patch('agent.inventario.uuid.getnode', return_value=0x010203040506):
        assert _mac_local() is None


def test_mac_local_formateada_si_es_real():
    with patch('agent.inventario.uuid.getnode', return_value=0xAABBCCDDEEFF):
        assert _mac_local() == 'AA:BB:CC:DD:EE:FF'
