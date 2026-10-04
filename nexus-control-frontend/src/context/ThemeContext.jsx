import { createContext, useContext, useEffect, useState, useCallback } from 'react'

const ThemeContext = createContext(null)

function resolveInitial() {
  if (typeof window === 'undefined') return 'dark'
  try {
    const saved = localStorage.getItem('theme')
    if (saved === 'dark' || saved === 'light') return saved
  } catch {}
  return 'dark'
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(resolveInitial)

  useEffect(() => {
    const root = document.documentElement

                                                                                
                                                                               
                                                                                
                                                                                
                                                                                
                                                                                
    const killTransitions = document.createElement('style')
    killTransitions.appendChild(
      document.createTextNode('*,*::before,*::after{transition:none!important;animation:none!important}')
    )
    document.head.appendChild(killTransitions)

    if (theme === 'dark') root.classList.add('dark')
    else root.classList.remove('dark')
    root.style.colorScheme = theme
    try { localStorage.setItem('theme', theme) } catch {}

                                                                           
    window.getComputedStyle(root).getPropertyValue('opacity')
                                                       
    const raf = window.requestAnimationFrame(() => {
      if (killTransitions.parentNode) killTransitions.parentNode.removeChild(killTransitions)
    })

    return () => {
      window.cancelAnimationFrame(raf)
      if (killTransitions.parentNode) killTransitions.parentNode.removeChild(killTransitions)
    }
  }, [theme])

  const setTheme = useCallback((value) => {
    setThemeState(value === 'dark' ? 'dark' : 'light')
  }, [])

  const toggleTheme = useCallback(() => {
    setThemeState((t) => (t === 'dark' ? 'light' : 'dark'))
  }, [])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  return useContext(ThemeContext) || { theme: 'dark', setTheme: () => {}, toggleTheme: () => {} }
}
