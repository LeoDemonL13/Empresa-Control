import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { LogOut, Moon, Search, Sun, User } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useTheme } from '../context/ThemeContext'
import MenuSearch from './MenuSearch'
import SysLabel from './ui/SysLabel'

function inicialesDe(nombre, username) {
  const base = (nombre || username || '?').trim()
  const partes = base.split(/\s+/).filter(Boolean)
  if (partes.length === 0) return '?'
  if (partes.length === 1) return partes[0].slice(0, 2).toUpperCase()
  return (partes[0][0] + partes[partes.length - 1][0]).toUpperCase()
}

export default function Topbar() {
  const { user, logout } = useAuth()
  const { theme, toggleTheme } = useTheme()
  const [buscarAbierto, setBuscarAbierto] = useState(false)
  const [menuAbierto, setMenuAbierto] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    function onKeyDown(e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        setBuscarAbierto(true)
      }
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [])

  useEffect(() => {
    function onClickAfuera(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setMenuAbierto(false)
      }
    }
    document.addEventListener('mousedown', onClickAfuera)
    return () => document.removeEventListener('mousedown', onClickAfuera)
  }, [])

  return (
    <header className="sticky top-0 z-20 flex h-16 flex-shrink-0 items-center gap-3 border-b border-ink-200 bg-white/90 px-4 backdrop-blur dark:border-obsidian-line dark:bg-obsidian-main/90 sm:px-6">
      <button
        type="button"
        onClick={() => setBuscarAbierto(true)}
        className="flex h-9 flex-1 max-w-sm items-center gap-2 rounded-md border border-ink-200 bg-ink-50 px-3 text-sm text-ink-500 transition-colors hover:border-ink-300 focus-ring dark:border-obsidian-line dark:bg-obsidian-cardAlt dark:text-obsidian-muted dark:hover:border-ink-600"
      >
        <Search size={15} />
        <span className="flex-1 text-left">Buscar productos, secciones...</span>
        <kbd className="nx-label rounded border border-ink-300 px-1.5 py-0.5 dark:border-ink-600">⌘K</kbd>
      </button>

      <div className="flex-1" />

      <SysLabel live className="hidden sm:inline-flex">
        en línea
      </SysLabel>

      <button
        type="button"
        onClick={toggleTheme}
        className="inline-flex h-9 w-9 items-center justify-center rounded-md text-ink-500 transition-colors hover:bg-ink-100 focus-ring dark:text-ink-300 dark:hover:bg-white/5"
        aria-label={theme === 'dark' ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
      >
        {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
      </button>

      <div className="relative" ref={menuRef}>
        <button
          type="button"
          onClick={() => setMenuAbierto((v) => !v)}
          className="flex items-center gap-2.5 rounded-md py-1 pl-1 pr-2 transition-colors hover:bg-ink-100 focus-ring dark:hover:bg-white/5"
        >
          <span className="inline-flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-xs font-semibold text-white">
            {inicialesDe(user?.full_name, user?.username)}
          </span>
          <span className="hidden text-left leading-tight sm:block">
            <span className="block text-sm font-medium text-ink-900 dark:text-white">
              {user?.full_name || user?.username}
            </span>
            <span className="block text-xs text-ink-500 dark:text-obsidian-muted">
              {user?.role === 'super_admin' ? 'Súper admin' : 'Administrador'}
            </span>
          </span>
        </button>

        {menuAbierto && (
          <div className="absolute right-0 top-full mt-2 w-48 animate-scale-in overflow-hidden rounded-md border border-ink-200 bg-white shadow-elevated dark:border-obsidian-line dark:bg-obsidian-card">
            <Link
              to="/perfil"
              onClick={() => setMenuAbierto(false)}
              className="flex items-center gap-2 px-3.5 py-2.5 text-sm text-ink-700 hover:bg-ink-100 dark:text-ink-200 dark:hover:bg-white/5"
            >
              <User size={15} /> Mi perfil
            </Link>
            <button
              type="button"
              onClick={() => {
                setMenuAbierto(false)
                logout()
              }}
              className="flex w-full items-center gap-2 border-t border-ink-200 px-3.5 py-2.5 text-sm text-red-600 hover:bg-red-50 dark:border-obsidian-line dark:text-red-400 dark:hover:bg-red-950/40"
            >
              <LogOut size={15} /> Cerrar sesión
            </button>
          </div>
        )}
      </div>

      <MenuSearch open={buscarAbierto} onClose={() => setBuscarAbierto(false)} role={user?.role} />
    </header>
  )
}
