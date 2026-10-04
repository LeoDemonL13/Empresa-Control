import api from './axios'

export function listarEquipos(params) {
  return api.get('/equipos', { params }).then((r) => r.data)
}

export function obtenerEquipo(id) {
  return api.get(`/equipos/${id}`).then((r) => r.data)
}

export function crearEquipo(payload) {
  return api.post('/equipos', payload).then((r) => r.data)
}

export function actualizarEquipo(id, payload) {
  return api.put(`/equipos/${id}`, payload).then((r) => r.data)
}

export function eliminarEquipo(id) {
  return api.delete(`/equipos/${id}`).then((r) => r.data)
}

export function regenerarEnrolamiento(id) {
  return api.post(`/equipos/${id}/enrolamiento`).then((r) => r.data)
}

export function listarAplicaciones(equipoId) {
  return api.get(`/equipos/${equipoId}/aplicaciones`).then((r) => r.data)
}

export function agregarAplicacion(equipoId, payload) {
  return api.post(`/equipos/${equipoId}/aplicaciones`, payload).then((r) => r.data)
}

export function actualizarPolitica(equipoId, aplicacionId, payload) {
  return api.put(`/equipos/${equipoId}/aplicaciones/${aplicacionId}`, payload).then((r) => r.data)
}

export function quitarAplicacion(equipoId, aplicacionId) {
  return api.delete(`/equipos/${equipoId}/aplicaciones/${aplicacionId}`).then((r) => r.data)
}

export function obtenerUso(equipoId, dias) {
  return api.get(`/equipos/${equipoId}/uso`, { params: dias ? { dias } : {} }).then((r) => r.data)
}

export function listarAppsInstaladas(equipoId) {
  return api.get(`/equipos/${equipoId}/apps-instaladas`).then((r) => r.data)
}
