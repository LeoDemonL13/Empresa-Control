import { useEffect, useState } from 'react'
import { Laptop, ShieldCheck, ShieldOff, Smartphone } from 'lucide-react'
import { Badge, Button, Card, CardHeader } from '../components/ui'
import Input, { Label } from '../components/ui/Input'
import Modal from '../components/ui/Modal'
import * as authApi from '../api/auth'
import { useAuth } from '../context/AuthContext'

function Alerta({ tipo = 'error', children }) {
  if (!children) return null
  const clases =
    tipo === 'error'
      ? 'bg-red-50 text-red-700 dark:bg-red-950/40 dark:text-red-300'
      : 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
  return <div className={`rounded-md px-3 py-2 text-sm ${clases}`}>{children}</div>
}

function SeccionDatos({ user, onActualizado }) {
  const [full_name, setFullName] = useState(user?.full_name || '')
  const [position, setPosition] = useState(user?.position || '')
  const [contact_info, setContactInfo] = useState(user?.contact_info || '')
  const [msg, setMsg] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function guardar(e) {
    e.preventDefault()
    setError('')
    setMsg('')
    setCargando(true)
    try {
      const actualizado = await authApi.actualizarPerfil({ full_name, position, contact_info })
      onActualizado(actualizado)
      setMsg('Perfil actualizado')
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo actualizar el perfil')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Card>
      <CardHeader title="Datos del perfil" description="Tu usuario es fijo; el resto puedes editarlo." />
      <form onSubmit={guardar} className="space-y-4">
        <div>
          <Label>Usuario</Label>
          <Input value={user?.username || ''} disabled />
        </div>
        <div>
          <Label>Nombre completo</Label>
          <Input value={full_name} onChange={(e) => setFullName(e.target.value)} />
        </div>
        <div>
          <Label>Puesto</Label>
          <Input value={position} onChange={(e) => setPosition(e.target.value)} />
        </div>
        <div>
          <Label>Contacto</Label>
          <Input value={contact_info} onChange={(e) => setContactInfo(e.target.value)} />
        </div>
        <Alerta>{error}</Alerta>
        <Alerta tipo="ok">{msg}</Alerta>
        <Button type="submit" loading={cargando}>
          Guardar
        </Button>
      </form>
    </Card>
  )
}

function SeccionPassword() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [code, setCode] = useState('')
  const [requiereCodigo, setRequiereCodigo] = useState(false)
  const [error, setError] = useState('')
  const [msg, setMsg] = useState('')
  const [cargando, setCargando] = useState(false)

  async function guardar(e) {
    e.preventDefault()
    setError('')
    setMsg('')
    setCargando(true)
    try {
      await authApi.cambiarPasswordPropia({ current_password: currentPassword, new_password: newPassword, code })
      setMsg('Contraseña actualizada. Tus otras sesiones se cerraron.')
      setCurrentPassword('')
      setNewPassword('')
      setCode('')
      setRequiereCodigo(false)
    } catch (err) {
      if (err.response?.data?.requires_totp) {
        setRequiereCodigo(true)
      }
      setError(err.response?.data?.error || 'No se pudo cambiar la contraseña')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Card>
      <CardHeader title="Contraseña" description="Mínimo 12 caracteres, con mayúsculas, minúsculas, números y símbolos." />
      <form onSubmit={guardar} className="space-y-4">
        <div>
          <Label>Contraseña actual</Label>
          <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
        </div>
        <div>
          <Label>Contraseña nueva</Label>
          <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
        </div>
        {requiereCodigo && (
          <div>
            <Label>Código 2FA</Label>
            <Input value={code} onChange={(e) => setCode(e.target.value)} required />
          </div>
        )}
        <Alerta>{error}</Alerta>
        <Alerta tipo="ok">{msg}</Alerta>
        <Button type="submit" loading={cargando}>
          Cambiar contraseña
        </Button>
      </form>
    </Card>
  )
}

function ModalActivar2FA({ open, onClose, onActivado }) {
  const [paso, setPaso] = useState('password')
  const [currentPassword, setCurrentPassword] = useState('')
  const [secret, setSecret] = useState('')
  const [qr, setQr] = useState('')
  const [code, setCode] = useState('')
  const [codigosRespaldo, setCodigosRespaldo] = useState(null)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  function reiniciar() {
    setPaso('password')
    setCurrentPassword('')
    setSecret('')
    setQr('')
    setCode('')
    setCodigosRespaldo(null)
    setError('')
  }

  async function pedirQr(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const data = await authApi.setup2fa(currentPassword)
      setSecret(data.secret)
      setQr(data.qr)
      setPaso('qr')
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo iniciar la configuración')
    } finally {
      setCargando(false)
    }
  }

  async function confirmar(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      await authApi.confirm2fa({ current_password: currentPassword, secret, code })
      const backup = await authApi.generarBackupCodes({ current_password: currentPassword, code })
      setCodigosRespaldo(backup.codes)
      setPaso('backup')
      onActivado()
    } catch (err) {
      setError(err.response?.data?.error || 'Código incorrecto')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={() => {
        reiniciar()
        onClose()
      }}
      title="Activar verificación en dos pasos"
    >
      {paso === 'password' && (
        <form onSubmit={pedirQr} className="space-y-4">
          <p className="text-sm text-ink-600 dark:text-ink-300">Confirma tu contraseña para generar el código QR.</p>
          <Input
            type="password"
            placeholder="Contraseña actual"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
          />
          <Alerta>{error}</Alerta>
          <Button type="submit" className="w-full" loading={cargando}>
            Continuar
          </Button>
        </form>
      )}

      {paso === 'qr' && (
        <form onSubmit={confirmar} className="space-y-4">
          <p className="text-sm text-ink-600 dark:text-ink-300">
            Escanea este código con tu app de autenticación y escribe el código de 6 dígitos.
          </p>
          <img src={`data:image/png;base64,${qr}`} alt="Código QR de 2FA" className="mx-auto h-44 w-44 rounded-md border border-ink-200 dark:border-obsidian-line" />
          <p className="text-center font-mono text-xs text-ink-500 dark:text-obsidian-muted">{secret}</p>
          <Input placeholder="000000" value={code} onChange={(e) => setCode(e.target.value)} required />
          <Alerta>{error}</Alerta>
          <Button type="submit" className="w-full" loading={cargando}>
            Activar
          </Button>
        </form>
      )}

      {paso === 'backup' && codigosRespaldo && (
        <div className="space-y-4">
          <Alerta tipo="ok">2FA activado. Guarda estos códigos de respaldo, se muestran una sola vez.</Alerta>
          <div className="grid grid-cols-2 gap-2 rounded-md bg-ink-50 p-3 font-mono text-sm dark:bg-obsidian-cardAlt">
            {codigosRespaldo.map((c) => (
              <span key={c}>{c}</span>
            ))}
          </div>
          <Button
            className="w-full"
            onClick={() => {
              reiniciar()
              onClose()
            }}
          >
            Listo
          </Button>
        </div>
      )}
    </Modal>
  )
}

function ModalDesactivar2FA({ open, onClose, onDesactivado }) {
  const [currentPassword, setCurrentPassword] = useState('')
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function desactivar(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      await authApi.disable2fa({ current_password: currentPassword, code })
      onDesactivado()
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo desactivar 2FA')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Desactivar verificación en dos pasos">
      <form onSubmit={desactivar} className="space-y-4">
        <Input type="password" placeholder="Contraseña actual" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} required />
        <Input placeholder="Código 2FA" value={code} onChange={(e) => setCode(e.target.value)} required />
        <Alerta>{error}</Alerta>
        <Button type="submit" variant="danger" className="w-full" loading={cargando}>
          Desactivar
        </Button>
      </form>
    </Modal>
  )
}

function SeccionDosFactores({ user, onActualizado }) {
  const [modal, setModal] = useState(null)
  const activo = Boolean(user?.totp_enabled)

  return (
    <Card>
      <CardHeader
        title="Verificación en dos pasos"
        description="Protege tu cuenta con un código temporal además de tu contraseña."
        actions={
          activo ? (
            <Badge tone="success" dot mono leftIcon={<ShieldCheck size={12} />}>
              Activo
            </Badge>
          ) : (
            <Badge tone="neutral" leftIcon={<ShieldOff size={12} />}>
              Inactivo
            </Badge>
          )
        }
      />
      {activo ? (
        <Button variant="danger-ghost" onClick={() => setModal('desactivar')}>
          Desactivar 2FA
        </Button>
      ) : (
        <Button onClick={() => setModal('activar')}>Activar 2FA</Button>
      )}

      <ModalActivar2FA
        open={modal === 'activar'}
        onClose={() => setModal(null)}
        onActivado={() => onActualizado({ ...user, totp_enabled: true })}
      />
      <ModalDesactivar2FA
        open={modal === 'desactivar'}
        onClose={() => setModal(null)}
        onDesactivado={() => onActualizado({ ...user, totp_enabled: false })}
      />
    </Card>
  )
}

function SeccionSesiones() {
  const [sesiones, setSesiones] = useState([])
  const [cargando, setCargando] = useState(true)

  function cargar() {
    authApi
      .listarSesiones()
      .then(setSesiones)
      .catch(() => {})
      .finally(() => setCargando(false))
  }

  useEffect(cargar, [])

  async function revocar(id) {
    await authApi.revocarSesion(id)
    cargar()
  }

  return (
    <Card>
      <CardHeader title="Sesiones activas" description="Dispositivos con acceso activo a tu cuenta." />
      {cargando && <p className="text-sm text-ink-500 dark:text-obsidian-muted">Cargando...</p>}
      <ul className="space-y-2">
        {sesiones.map((s) => (
          <li key={s.id} className="flex items-center justify-between gap-3 border-b border-ink-100 py-2 text-sm last:border-0 dark:border-obsidian-line">
            <div className="flex items-center gap-2 text-ink-700 dark:text-ink-200">
              {(s.user_agent || '').toLowerCase().includes('mobile') ? <Smartphone size={15} /> : <Laptop size={15} />}
              <span className="truncate">{s.ip || 'IP desconocida'}</span>
            </div>
            <Button size="xs" variant="danger-ghost" onClick={() => revocar(s.id)}>
              Cerrar
            </Button>
          </li>
        ))}
      </ul>
    </Card>
  )
}

export default function Perfil() {
  const { user, setUser } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900 dark:text-white">Mi perfil</h1>
        <p className="mt-1 text-sm text-ink-500 dark:text-obsidian-muted">Administra tu cuenta y tu seguridad.</p>
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-6">
          <SeccionDatos user={user} onActualizado={setUser} />
          <SeccionPassword />
        </div>
        <div className="space-y-6">
          <SeccionDosFactores user={user} onActualizado={setUser} />
          <SeccionSesiones />
        </div>
      </div>
    </div>
  )
}
