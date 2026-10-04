import api from './axios'

export function listarConexiones() {
  return api.get('/conexiones-sociales').then((r) => r.data)
}

export function guardarConexion(plataforma, credenciales) {
  return api.put(`/conexiones-sociales/${plataforma}`, credenciales).then((r) => r.data)
}

export function eliminarConexion(plataforma) {
  return api.delete(`/conexiones-sociales/${plataforma}`).then((r) => r.data)
}

export function sincronizarConexion(plataforma) {
  return api.post(`/conexiones-sociales/${plataforma}/sincronizar`).then((r) => r.data)
}

export function sincronizarTodas() {
  return api.post('/conexiones-sociales/sincronizar-todas').then((r) => r.data)
}
