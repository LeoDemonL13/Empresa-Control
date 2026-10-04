import api from './axios'

export function listarBitacora(params) {
  return api.get('/bitacora', { params }).then((r) => r.data)
}

export function detalleBitacora(id) {
  return api.get(`/bitacora/${id}`).then((r) => r.data)
}
