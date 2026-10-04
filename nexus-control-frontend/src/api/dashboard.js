import api from './axios'

export function obtenerResumen() {
  return api.get('/dashboard/resumen').then((r) => r.data)
}
