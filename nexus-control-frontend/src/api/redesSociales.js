import api from './axios'

export function listarConexiones() {
  return api.get('/redes-sociales').then((r) => r.data)
}

export function obtenerUrlConexion(plataforma) {
  return api.get(`/redes-sociales/${plataforma}/conectar`).then((r) => r.data)
}

export function actualizarSeguimientoCuenta(plataforma, cuentaId, seguimientoActivo) {
  return api
    .put(`/redes-sociales/${plataforma}/cuentas/${cuentaId}/seguimiento`, { seguimiento_activo: seguimientoActivo })
    .then((r) => r.data)
}

export function sincronizarConexion(plataforma) {
  return api.post(`/redes-sociales/${plataforma}/sincronizar`).then((r) => r.data)
}

export function sincronizarTodas() {
  return api.post('/redes-sociales/sincronizar-todas').then((r) => r.data)
}

export function desconectarConexion(plataforma, purgarHistorico = false) {
  return api.post(`/redes-sociales/${plataforma}/desconectar`, { purgar_historico: purgarHistorico }).then((r) => r.data)
}

export function obtenerSalud(plataforma) {
  return api.get(`/redes-sociales/${plataforma}/salud`).then((r) => r.data)
}

export function obtenerEstadoSistema() {
  return api.get('/redes-sociales/sistema').then((r) => r.data)
}

export function obtenerResumen({ rango = '7d', plataforma, desde, hasta } = {}) {
  const params = { rango }
  if (plataforma) params.plataforma = plataforma
  if (rango === 'custom') {
    params.desde = desde
    params.hasta = hasta
  }
  return api.get('/redes-sociales/resumen', { params }).then((r) => r.data)
}
