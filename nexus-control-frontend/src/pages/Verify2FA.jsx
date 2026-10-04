import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { ShieldAlert, ShieldCheck } from 'lucide-react'
import BrandMark from '../components/BrandMark'
import { Button, SysLabel } from '../components/ui'
import Input, { Label } from '../components/ui/Input'
import { useAuth } from '../context/AuthContext'

export default function Verify2FA() {
  const { verify2fa } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const stepToken = location.state?.stepToken

  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  if (!stepToken) {
    navigate('/login', { replace: true })
    return null
  }

  async function onSubmit(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      await verify2fa(stepToken, code.trim())
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.response?.data?.error || 'Código incorrecto')
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
          <div className="mb-5 flex items-center gap-2">
            <ShieldCheck size={18} className="text-brand-400" />
            <h1 className="text-lg font-semibold text-white">Verificación en dos pasos</h1>
          </div>
          <p className="mb-5 text-sm text-ink-400">
            Ingresa el código de tu aplicación de autenticación, o uno de tus códigos de respaldo.
          </p>

          <form onSubmit={onSubmit} className="space-y-4">
            <div>
              <Label className="text-ink-300">Código</Label>
              <Input
                autoFocus
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="000000"
                inputMode="text"
                autoComplete="one-time-code"
                maxLength={32}
                required
              />
            </div>

            {error && (
              <div className="flex items-start gap-2 rounded-md bg-red-950/40 px-3 py-2 text-sm text-red-300">
                <ShieldAlert size={16} className="mt-0.5 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Button type="submit" className="w-full" size="lg" loading={cargando}>
              Verificar
            </Button>
            <button
              type="button"
              onClick={() => navigate('/login', { replace: true })}
              className="w-full text-center text-xs text-ink-500 hover:text-ink-300"
            >
              Volver a intentar con otra cuenta
            </button>
          </form>
        </div>
        <p className="mt-6 text-center">
          <SysLabel>sec protected</SysLabel>
        </p>
      </div>
    </div>
  )
}
