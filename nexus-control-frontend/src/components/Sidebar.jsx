import { NavLink } from 'react-router-dom'
import BrandMark from './BrandMark'
import { menuParaRol } from '../config/menus'

export default function Sidebar({ role }) {
  const grupos = menuParaRol(role)

  return (
    <aside className="hidden w-64 flex-shrink-0 overflow-y-auto border-r border-white/5 bg-obsidian-sidebar scrollbar-dark lg:flex lg:flex-col">
      <div className="flex h-16 flex-shrink-0 items-center border-b border-white/5 px-4">
        <BrandMark />
      </div>
      <nav className="flex-1 py-3">
        {grupos.map((grupo) => (
          <div key={grupo.label} className="mb-3">
            <p className="nx-nav-section text-ink-400/70">{grupo.label}</p>
            <div className="space-y-0.5">
              {grupo.items.map((item) => {
                const Icon = item.icon
                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    end={item.end}
                    className={({ isActive }) =>
                      `relative mx-2 flex items-center gap-3 rounded-md px-2.5 py-2 text-sm transition-colors focus-ring ${
                        isActive
                          ? 'bg-white/10 font-medium text-white'
                          : 'text-ink-300 hover:bg-white/5 hover:text-white'
                      }`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {isActive && (
                          <span className="absolute bottom-1.5 left-0 top-1.5 w-0.5 rounded-r-full bg-brand-300" />
                        )}
                        <Icon size={18} strokeWidth={1.75} className="flex-shrink-0" />
                        <span className="truncate">{item.label}</span>
                      </>
                    )}
                  </NavLink>
                )
              })}
            </div>
          </div>
        ))}
      </nav>
    </aside>
  )
}
