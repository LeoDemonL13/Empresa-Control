from unittest.mock import Mock, patch

import pytest
import requests

from agent.cliente_api import ClienteAPI, ErrorAPI


def _respuesta(ok, status_code=200, json_data=None, text=''):
    r = Mock()
    r.ok = ok
    r.status_code = status_code
    r.json = Mock(return_value=json_data or {})
    r.text = text
    return r


def test_enrolar_exitoso():
    cliente = ClienteAPI('http://localhost:5001')
    with patch('agent.cliente_api.requests.post', return_value=_respuesta(True, json_data={'equipo_id': 1, 'api_key': 'k', 'nombre': 'PC'})):
        resultado = cliente.enrolar('ABCDE-FGHIJ')
    assert resultado['equipo_id'] == 1


def test_enrolar_codigo_invalido_lanza_error_api():
    cliente = ClienteAPI('http://localhost:5001')
    with patch('agent.cliente_api.requests.post', return_value=_respuesta(False, 400, {'error': 'Código inválido o expirado'})):
        with pytest.raises(ErrorAPI, match='inválido'):
            cliente.enrolar('ZZZZZ-ZZZZZ')


def test_enrolar_sin_conexion_lanza_error_api():
    cliente = ClienteAPI('http://localhost:5001')
    with patch('agent.cliente_api.requests.post', side_effect=requests.ConnectionError('refused')):
        with pytest.raises(ErrorAPI, match='No se pudo contactar'):
            cliente.enrolar('ABCDE-FGHIJ')


def test_enviar_inventario_incluye_cabeceras_y_version():
    cliente = ClienteAPI('http://localhost:5001', equipo_id=9, api_key='clave')
    mock_post = Mock(return_value=_respuesta(True, json_data={'ok': True}))
    with patch('agent.cliente_api.requests.post', mock_post):
        cliente.enviar_inventario({'hostname': 'PC-1'})
    _, kwargs = mock_post.call_args
    assert kwargs['headers'] == {'X-Device-Id': '9', 'X-Api-Key': 'clave'}
    assert kwargs['json']['hostname'] == 'PC-1'
    assert 'agente_version' in kwargs['json']


def test_enviar_inventario_error_del_servidor():
    cliente = ClienteAPI('http://localhost:5001', equipo_id=9, api_key='clave')
    with patch('agent.cliente_api.requests.post', return_value=_respuesta(False, 409, {'error': 'MAC duplicada'})):
        with pytest.raises(ErrorAPI, match='MAC duplicada'):
            cliente.enviar_inventario({'mac': 'AA:BB:CC:DD:EE:FF'})
