import { useEffect, useState } from 'react'
import { KeyRound, Plus, Power, PowerOff, ShieldCheck, ShieldOff } from 'lucide-react'
import { Badge, Button, Card } from '../components/ui'
import Input, { Label } from '../components/ui/Input'
import Modal from '../components/ui/Modal'
import * as usersApi from '../api/users'
import { useAuth } from '../context/AuthContext'

function Alerta({ children }) {
  if (!children) return null
  return <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">{children}</div>
}

function ModalCrear({ open, onClose, onCreado }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [full_name, setFullName] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function crear(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      await usersApi.crearAdministrador({ username, password, full_name })
      setUsername('')
      setPassword('')
      setFullName('')
      onCreado()
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo crear el administrador')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title="Nuevo administrador">
      <form onSubmit={crear} className="space-y-4">
        <div>
          <Label>Usuario</Label>
          <Input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="usuario@nexus.mx" required />
        </div>
        <div>
          <Label>Nombre completo</Label>
          <Input value={full_name} onChange={(e) => setFullName(e.target.value)} placeholder="Nombre y apellido" />
        </div>
        <div>
          <Label>Contraseña temporal</Label>
          <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mínimo 12 caracteres" required />
        </div>
        <Alerta>{error}</Alerta>
        <Button type="submit" className="w-full" loading={cargando}>
          Crear administrador
        </Button>
      </form>
    </Modal>
  )
}

function ModalResetPassword({ admin, onClose, onListo }) {
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  async function guardar(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      await usersApi.resetearPassword(admin.id, password)
      onListo()
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo restablecer la contraseña')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Modal open={Boolean(admin)} onClose={onClose} title={`Restablecer contraseña de ${admin?.username || ''}`}>
      <form onSubmit={guardar} className="space-y-4">
        <Input type="password" placeholder="Contraseña nueva" value={password} onChange={(e) => setPassword(e.target.value)} required />
        <Alerta>{error}</Alerta>
        <Button type="submit" className="w-full" loading={cargando}>
          Guardar
        </Button>
      </form>
    </Modal>
  )
}

export default function Usuarios() {
  const { user: yo } = useAuth()
  const [administradores, setAdministradores] = useState([])
  const [cargando, setCargando] = useState(true)
  const [modalCrear, setModalCrear] = useState(false)
  const [resetTarget, setResetTarget] = useState(null)
  const [error, setError] = useState('')

  function cargar() {
    setCargando(true)
    usersApi
      .listarAdministradores()
      .then(setAdministradores)
      .catch((err) => setError(err.response?.data?.error || 'No se pudo cargar la lista'))
      .finally(() => setCargando(false))
  }

  useEffect(cargar, [])

  async function alternarActivo(admin) {
    if (admin.activo) {
      await usersApi.desactivarAdministrador(admin.id)
    } else {
      await usersApi.reactivarAdministrador(admin.id)
    }
    cargar()
  }

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink-900 dark:text-white">Administradores</h1>
          <p className="mt-1 text-sm text-ink-500 dark:text-obsidian-muted">Altas, bajas y permisos. Exclusivo del súper administrador.</p>
        </div>
        <Button leftIcon={<Plus size={16} />} onClick={() => setModalCrear(true)}>
          Agregar
        </Button>
      </div>

      <Alerta>{error}</Alerta>

      <Card padded={false}>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-200 text-left text-xs uppercase tracking-wide text-ink-500 dark:border-obsidian-line dark:text-obsidian-muted">
                <th className="px-4 py-3">Usuario</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">2FA</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {cargando && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-ink-500 dark:text-obsidian-muted">
                    Cargando...
                  </td>
                </tr>
              )}
              {!cargando &&
                administradores.map((a) => (
                  <tr key={a.id} className="border-b border-ink-100 last:border-0 dark:border-obsidian-line">
                    <td className="px-4 py-3">
                      <p className="font-medium text-ink-900 dark:text-white">{a.full_name || a.username}</p>
                      <p className="text-xs text-ink-500 dark:text-obsidian-muted">{a.username}</p>
                    </td>
                    <td className="px-4 py-3">
                      <Badge tone={a.role === 'super_admin' ? 'brand' : 'neutral'}>
                        {a.role === 'super_admin' ? 'Súper admin' : 'Administrador'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      {a.totp_enabled ? (
                        <Badge tone="success" leftIcon={<ShieldCheck size={12} />}>Sí</Badge>
                      ) : (
                        <Badge tone="neutral" leftIcon={<ShieldOff size={12} />}>No</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <Badge tone={a.activo ? 'success' : 'neutral'} dot mono>
                        {a.activo ? 'Activo' : 'Inactivo'}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-1.5">
                        <Button size="icon-sm" variant="ghost" title="Restablecer contraseña" onClick={() => setResetTarget(a)}>
                          <KeyRound size={15} />
                        </Button>
                        {a.id !== yo?.id && (
                          <Button
                            size="icon-sm"
                            variant="ghost"
                            title={a.activo ? 'Desactivar' : 'Reactivar'}
                            onClick={() => alternarActivo(a)}
                          >
                            {a.activo ? <PowerOff size={15} className="text-red-500" /> : <Power size={15} className="text-emerald-500" />}
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      </Card>

      <ModalCrear open={modalCrear} onClose={() => setModalCrear(false)} onCreado={cargar} />
      <ModalResetPassword admin={resetTarget} onClose={() => setResetTarget(null)} onListo={cargar} />
    </div>
  )
}
