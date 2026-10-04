import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function RequiereSesion() {
  const { autenticado, cargando } = useAuth()
  const location = useLocation()

  if (cargando) {
    return (
      <div className="flex h-screen items-center justify-center bg-obsidian-main">
        <p className="nx-label text-obsidian-muted">cargando-sesion.sys</p>
      </div>
    )
  }
  if (!autenticado) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }
  return <Outlet />
}

export function RequiereRol({ roles }) {
  const { user } = useAuth()
  if (!roles.includes(user?.role)) {
    return <Navigate to="/" replace />
  }
  return <Outlet />
}
