export function comandosParaRol(role) {
  const base = [
    { id: 'inicio', label: 'Inicio', path: '/', keywords: 'dashboard resumen' },
    { id: 'perfil', label: 'Mi perfil', path: '/perfil', keywords: 'cuenta password 2fa' },
    { id: 'equipos', label: 'Equipos', path: '/equipos', keywords: 'dispositivos computadoras' },
    { id: 'reportes', label: 'Reportes', path: '/reportes', keywords: 'pdf excel csv' },
    { id: 'bitacora', label: 'Bitácora', path: '/bitacora', keywords: 'auditoria logs historial' },
  ]
  if (role === 'super_admin') {
    base.push({ id: 'administradores', label: 'Administradores', path: '/administradores', keywords: 'usuarios admins' })
  }
  return base
}
