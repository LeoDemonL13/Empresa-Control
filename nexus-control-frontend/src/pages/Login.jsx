import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, ShieldAlert } from 'lucide-react'
import BrandMark from '../components/BrandMark'
import { Button, SysLabel } from '../components/ui'
import Input, { Label } from '../components/ui/Input'
import { useAuth } from '../context/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [verPassword, setVerPassword] = useState(false)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const resultado = await login(username, password)
      if (resultado.requires2fa) {
        navigate('/verificar-2fa', { state: { stepToken: resultado.stepToken } })
      } else {
        navigate('/', { replace: true })
      }
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo iniciar sesión')
    } finally {
      setCargando(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-obsidian-main px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <BrandMark size="lg" />
        </div>

        <div className="nx-surface p-6">
          <div className="mb-5 flex items-center justify-between">
            <h1 className="text-lg font-semibold text-white">Iniciar sesión</h1>
            <SysLabel live>panel-operativo.sys</SysLabel>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <Label className="text-ink-300">Usuario</Label>
              <Input
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoComplete="username"
                placeholder="tu.usuario"
                required
              />
            </div>
            <div>
              <Label className="text-ink-300">Contraseña</Label>
              <div className="relative">
                <Input
                  type={verPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  placeholder="••••••••••••"
                  className="pr-9"
                  required
                />
                <button
                  type="button"
                  onClick={() => setVerPassword((v) => !v)}
                  className="absolute inset-y-0 right-0 flex w-9 items-center justify-center text-ink-500 hover:text-ink-300"
                  aria-label={verPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                >
                  {verPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-start gap-2 rounded-md bg-red-950/40 px-3 py-2 text-sm text-red-300">
                <ShieldAlert size={16} className="mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Button type="submit" className="w-full" size="lg" loading={cargando}>
              Entrar
            </Button>
          </form>
        </div>

        <p className="mt-6 text-center text-xs text-ink-500">Nexus Obsidian Control · Acceso restringido</p>
      </div>
    </div>
  )
}
