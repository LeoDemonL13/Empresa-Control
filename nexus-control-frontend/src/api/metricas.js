import api from './axios'

export function listarMetricas() {
  return api.get('/metricas-sociales').then((r) => r.data)
}

export function guardarMetrica(payload) {
  return api.post('/metricas-sociales', payload).then((r) => r.data)
}

export function eliminarMetrica(id) {
  return api.delete(`/metricas-sociales/${id}`).then((r) => r.data)
}
