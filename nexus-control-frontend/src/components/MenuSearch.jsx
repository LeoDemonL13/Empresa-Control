import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search } from 'lucide-react'
import { menuParaRol } from '../config/menus'

export default function MenuSearch({ open, onClose, role }) {
  const [query, setQuery] = useState('')
  const [activo, setActivo] = useState(0)
  const inputRef = useRef(null)
  const navigate = useNavigate()

  const items = useMemo(() => menuParaRol(role).flatMap((g) => g.items), [role])
  const filtrados = useMemo(() => {
    const q = query.trim().toLowerCase()
    if (!q) return items
    return items.filter((i) => i.label.toLowerCase().includes(q))
  }, [items, query])

  useEffect(() => {
    if (open) {
      setQuery('')
      setActivo(0)
      requestAnimationFrame(() => inputRef.current?.focus())
    }
  }, [open])

  useEffect(() => {
    setActivo(0)
  }, [query])

  if (!open) return null

  function ir(item) {
    if (!item) return
    navigate(item.path)
    onClose()
  }

  function onKeyDown(e) {
    if (e.key === 'Escape') {
      onClose()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActivo((v) => Math.min(v + 1, filtrados.length - 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActivo((v) => Math.max(v - 1, 0))
    } else if (e.key === 'Enter') {
      e.preventDefault()
      ir(filtrados[activo])
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/50 pt-24" onClick={onClose}>
      <div
        className="w-full max-w-lg animate-scale-in overflow-hidden rounded-xl border border-ink-200 bg-white shadow-modal dark:border-obsidian-line dark:bg-obsidian-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 border-b border-ink-200 px-4 py-3 dark:border-obsidian-line">
          <Search size={16} className="text-ink-400" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Buscar una sección..."
            className="w-full bg-transparent text-sm text-ink-900 placeholder:text-ink-400 focus:outline-none dark:text-white"
          />
          <kbd className="nx-label rounded border border-ink-200 px-1.5 py-0.5 dark:border-obsidian-line">esc</kbd>
        </div>
        <div className="max-h-72 overflow-y-auto scrollbar-thin p-1.5">
          {filtrados.length === 0 && (
            <p className="px-3 py-6 text-center text-sm text-ink-500 dark:text-obsidian-muted">Sin resultados</p>
          )}
          {filtrados.map((item, idx) => {
            const Icon = item.icon
            return (
              <button
                key={item.path}
                type="button"
                onMouseEnter={() => setActivo(idx)}
                onClick={() => ir(item)}
                className={`flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-sm ${
                  idx === activo
                    ? 'bg-ink-100 text-ink-900 dark:bg-white/10 dark:text-white'
                    : 'text-ink-700 dark:text-ink-300'
                }`}
              >
                <Icon size={16} strokeWidth={1.75} />
                {item.label}
              </button>
            )
          })}
        </div>
      </div>
    </div>
  )
}
