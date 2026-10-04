import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import api from '../api/axios'
import * as authApi from '../api/auth'

const AuthContext = createContext(null)

const RUTAS_AUTH_PUBLICAS = ['/auth/login', '/auth/verify-2fa', '/auth/refresh']

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setTokenState] = useState(null)
  const [cargando, setCargando] = useState(true)
  const tokenRef = useRef(null)

  const aplicarSesion = useCallback((data) => {
    tokenRef.current = data.token
    setTokenState(data.token)
    setUser(data.user)
  }, [])

  const limpiarSesion = useCallback(() => {
    tokenRef.current = null
    setTokenState(null)
    setUser(null)
  }, [])

  useEffect(() => {
    const reqId = api.interceptors.request.use((config) => {
      if (tokenRef.current) {
        config.headers.Authorization = `Bearer ${tokenRef.current}`
      }
      return config
    })

    const resId = api.interceptors.response.use(
      (r) => r,
      async (error) => {
        const original = error.config
        const status = error.response?.status
        const esRutaPublica = RUTAS_AUTH_PUBLICAS.some((p) => original?.url?.endsWith(p))

        if (status === 401 && original && !original._reintentado && !esRutaPublica) {
          original._reintentado = true
          try {
            const data = await authApi.refresh()
            aplicarSesion(data)
            original.headers = original.headers || {}
            original.headers.Authorization = `Bearer ${data.token}`
            return api(original)
          } catch {
            limpiarSesion()
          }
        }
        return Promise.reject(error)
      },
    )

    return () => {
      api.interceptors.request.eject(reqId)
      api.interceptors.response.eject(resId)
    }
  }, [aplicarSesion, limpiarSesion])

  useEffect(() => {
    authApi
      .refresh()
      .then(aplicarSesion)
      .catch(() => {})
      .finally(() => setCargando(false))
  }, [aplicarSesion])

  const login = useCallback(
    async (username, password) => {
      const data = await authApi.login(username, password)
      if (data.requires2fa) {
        return { requires2fa: true, stepToken: data.stepToken }
      }
      aplicarSesion(data)
      return { requires2fa: false }
    },
    [aplicarSesion],
  )

  const verify2fa = useCallback(
    async (stepToken, code) => {
      const data = await authApi.verify2fa(stepToken, code)
      aplicarSesion(data)
    },
    [aplicarSesion],
  )

  const logout = useCallback(async () => {
    try {
      await authApi.logout()
    } finally {
      limpiarSesion()
    }
  }, [limpiarSesion])

  const value = {
    user,
    token,
    cargando,
    autenticado: Boolean(user),
    login,
    verify2fa,
    logout,
    setUser,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuth debe usarse dentro de AuthProvider')
  }
  return ctx
}
