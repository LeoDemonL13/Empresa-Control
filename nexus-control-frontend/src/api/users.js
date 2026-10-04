import api from './axios'

export function listarAdministradores() {
  return api.get('/users').then((r) => r.data)
}

export function crearAdministrador(payload) {
  return api.post('/users', payload).then((r) => r.data)
}

export function actualizarAdministrador(id, payload) {
  return api.put(`/users/${id}`, payload).then((r) => r.data)
}

export function desactivarAdministrador(id) {
  return api.delete(`/users/${id}`).then((r) => r.data)
}

export function reactivarAdministrador(id) {
  return api.post(`/users/${id}/reactivar`).then((r) => r.data)
}

export function resetearPassword(id, newPassword) {
  return api.post(`/users/${id}/password`, { new_password: newPassword }).then((r) => r.data)
}

export function revocarSesionesDe(id) {
  return api.delete(`/users/${id}/sessions`).then((r) => r.data)
}
