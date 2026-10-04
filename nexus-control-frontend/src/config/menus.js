import { Home, User, MonitorSmartphone, Share2, FileBarChart, UserCog, History } from 'lucide-react'

export const MENU_ADMIN = [
  {
    label: 'Cuenta',
    items: [
      { path: '/', label: 'Inicio', icon: Home, end: true },
      { path: '/perfil', label: 'Mi perfil', icon: User },
    ],
  },
  {
    label: 'Operación',
    items: [
      { path: '/equipos', label: 'Equipos', icon: MonitorSmartphone },
      { path: '/redes-sociales', label: 'Redes sociales', icon: Share2 },
      { path: '/reportes', label: 'Reportes', icon: FileBarChart },
    ],
  },
  {
    label: 'Administración',
    items: [
      { path: '/administradores', label: 'Administradores', icon: UserCog, soloSuperAdmin: true },
      { path: '/bitacora', label: 'Bitácora', icon: History },
    ],
  },
]

export function menuParaRol(role) {
  const esSuperAdmin = role === 'super_admin'
  return MENU_ADMIN.map((grupo) => ({
    ...grupo,
    items: grupo.items.filter((item) => !item.soloSuperAdmin || esSuperAdmin),
  })).filter((grupo) => grupo.items.length > 0)
}

export function todosLosItems() {
  return MENU_ADMIN.flatMap((grupo) => grupo.items)
}

export function rutaPermitida(role, path) {
  const item = todosLosItems().find((i) => i.path === path)
  if (!item) return true
  return !item.soloSuperAdmin || role === 'super_admin'
}
