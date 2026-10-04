import api from './axios'

export function login(username, password) {
  return api.post('/auth/login', { username, password }).then((r) => r.data)
}

export function verify2fa(stepToken, code) {
  return api.post('/auth/verify-2fa', { stepToken, code }).then((r) => r.data)
}

export function refresh() {
  return api.post('/auth/refresh').then((r) => r.data)
}

export function logout() {
  return api.post('/auth/logout').then((r) => r.data)
}

export function getPerfil() {
  return api.get('/auth/perfil').then((r) => r.data)
}

export function actualizarPerfil(payload) {
  return api.put('/auth/perfil', payload).then((r) => r.data)
}

export function actividadReciente(limit = 10) {
  return api.get('/auth/perfil/actividad', { params: { limit } }).then((r) => r.data)
}

export function cambiarPasswordPropia(payload) {
  return api.put('/auth/perfil/password', payload).then((r) => r.data)
}

export function setup2fa(currentPassword) {
  return api.post('/auth/setup-2fa', { current_password: currentPassword }).then((r) => r.data)
}

export function confirm2fa(payload) {
  return api.post('/auth/confirm-2fa', payload).then((r) => r.data)
}

export function disable2fa(payload) {
  return api.post('/auth/disable-2fa', payload).then((r) => r.data)
}

export function backupCodesEstado() {
  return api.get('/auth/backup-codes').then((r) => r.data)
}

export function generarBackupCodes(payload) {
  return api.post('/auth/backup-codes', payload).then((r) => r.data)
}

export function revocarBackupCodes(payload) {
  return api.delete('/auth/backup-codes', { data: payload }).then((r) => r.data)
}

export function listarSesiones() {
  return api.get('/auth/sesiones').then((r) => r.data)
}

export function revocarSesion(id) {
  return api.delete(`/auth/sesiones/${id}`).then((r) => r.data)
}

export function revocarTodasLasSesiones() {
  return api.delete('/auth/sesiones').then((r) => r.data)
}

export function estadoSeguridad() {
  return api.get('/auth/estado-seguridad').then((r) => r.data)
}
