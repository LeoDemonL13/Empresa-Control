import { useEffect, useState } from 'react'
import { Loader2, RefreshCw, Settings, Unlink } from 'lucide-react'
import toast from 'react-hot-toast'
import { Badge, Button, Card, CardHeader, Modal } from '../components/ui'
import Input, { Label } from '../components/ui/Input'
import * as conexionesApi from '../api/conexionesSociales'
import { useAuth } from '../context/AuthContext'
import { useSocket } from '../context/SocketContext'

const PLATAFORMAS = [
  { id: 'facebook', nombre: 'Facebook', color: 'bg-[#1877F2]' },
  { id: 'instagram', nombre: 'Instagram', color: 'bg-gradient-to-br from-[#F58529] via-[#DD2A7B] to-[#8134AF]' },
  { id: 'tiktok', nombre: 'TikTok', color: 'bg-ink-900' },
  { id: 'youtube', nombre: 'YouTube', color: 'bg-[#FF0000]' },
  { id: 'x', nombre: 'X', color: 'bg-ink-900' },
]

const CAMPOS_POR_PLATAFORMA = {
  facebook: [
    { campo: 'token_acceso', etiqueta: 'Token de acceso de la página (de larga duración)', tipo: 'password', placeholder: 'EAAxxXXxxXXXX...' },
    { campo: 'id_pagina', etiqueta: 'ID de la página de Facebook', tipo: 'text', placeholder: '123456789012345' },
  ],
  instagram: [
    { campo: 'token_acceso', etiqueta: 'Token de acceso (el de la página de Facebook vinculada)', tipo: 'password', placeholder: 'EAAxxXXxxXXXX...' },
    { campo: 'id_cuenta_negocio', etiqueta: 'ID de la cuenta de Instagram Business', tipo: 'text', placeholder: '178414...' },
  ],
  tiktok: [
    { campo: 'client_key', etiqueta: 'Client Key', tipo: 'text', placeholder: 'aw1a2b3c4d5e6f7g' },
    { campo: 'client_secret', etiqueta: 'Client Secret', tipo: 'password', placeholder: '••••••••••••••••' },
    { campo: 'token_actualizacion', etiqueta: 'Refresh Token', tipo: 'password', placeholder: 'rft.xxxxxxxxxxxx' },
  ],
  youtube: [
    { campo: 'clave_api', etiqueta: 'Clave de API de YouTube Data v3', tipo: 'password', placeholder: 'AIzaSy...' },
    { campo: 'id_canal', etiqueta: 'ID del canal (empieza con UC...)', tipo: 'text', placeholder: 'UCxxxxxxxxxxxxxxxxxxxxxx' },
  ],
  x: [
    { campo: 'bearer_token', etiqueta: 'Bearer Token (App-only)', tipo: 'password', placeholder: 'AAAAAAAAAAAAAAAAAAAAA...' },
    { campo: 'nombre_usuario', etiqueta: 'Usuario de la cuenta (sin @)', tipo: 'text', placeholder: 'mi_empresa' },
  ],
}

function nombrePlataforma(id) {
  return PLATAFORMAS.find((p) => p.id === id)?.nombre || id
}

function formatearFecha(iso) {
  if (!iso) return 'Nunca'
  return new Date(iso).toLocaleString('es-MX')
}

function Insignia({ plataforma }) {
  const info = PLATAFORMAS.find((p) => p.id === plataforma)
  return (
    <span
      className={`inline-flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg text-sm font-bold text-white ${info?.color || 'bg-ink-400'}`}
    >
      {info?.nombre?.[0] || '?'}
    </span>
  )
}

function ModalCredenciales({ open, onClose, plataforma, onGuardado }) {
  const campos = CAMPOS_POR_PLATAFORMA[plataforma] || []
  const [form, setForm] = useState({})
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    setForm({})
    setError('')
  }, [plataforma, open])

  async function guardar(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      await conexionesApi.guardarConexion(plataforma, form)
      toast.success('Credenciales guardadas. Ya puedes sincronizar.')
      onGuardado()
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudieron guardar las credenciales')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title={`Conectar ${nombrePlataforma(plataforma)}`}
      description="Quedan cifradas en el servidor y fijas: el sistema las usa para sincronizar solo, sin volver a pedirlas."
    >
      <form onSubmit={guardar} className="space-y-4">
        {campos.map((c) => (
          <div key={c.campo}>
            <Label>{c.etiqueta}</Label>
            <Input
              type={c.tipo}
              placeholder={c.placeholder}
              value={form[c.campo] || ''}
              onChange={(e) => setForm((f) => ({ ...f, [c.campo]: e.target.value }))}
              autoComplete="off"
              required
            />
          </div>
        ))}
        {error && (
          <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">
            {error}
          </div>
        )}
        <Button type="submit" className="w-full" loading={cargando}>
          Guardar credenciales
        </Button>
      </form>
    </Modal>
  )
}

function TarjetaConexion({ conexion, esSuperAdmin, onConfigurar, onSincronizar, onDesconectar, sincronizando }) {
  return (
    <div className="rounded-lg border border-ink-200 p-4 dark:border-obsidian-line">
      <div className="flex items-center gap-3">
        <Insignia plataforma={conexion.plataforma} />
        <div>
          <p className="font-semibold text-ink-900 dark:text-white">{nombrePlataforma(conexion.plataforma)}</p>
          <Badge tone={conexion.conectada ? 'success' : 'neutral'} dot>
            {conexion.conectada ? 'Conectada' : 'No conectada'}
          </Badge>
        </div>
      </div>

      <dl className="mt-3 space-y-1 text-xs text-ink-500 dark:text-obsidian-muted">
        <div className="flex justify-between">
          <dt>Última sincronización</dt>
          <dd>{formatearFecha(conexion.ultima_sincronizacion)}</dd>
        </div>
      </dl>

      {conexion.ultimo_error && (
        <p className="mt-2 rounded-md bg-red-50 px-2 py-1.5 text-xs text-red-700 dark:bg-red-950/40 dark:text-red-300">
          {conexion.ultimo_error}
        </p>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {esSuperAdmin && (
          <Button
            size="xs"
            variant="secondary"
            leftIcon={<Settings size={12} />}
            onClick={() => onConfigurar(conexion.plataforma)}
          >
            {conexion.conectada ? 'Editar credenciales' : 'Configurar'}
          </Button>
        )}
        {conexion.conectada && (
          <Button
            size="xs"
            variant="ghost"
            leftIcon={sincronizando ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
            disabled={sincronizando}
            onClick={() => onSincronizar(conexion.plataforma)}
          >
            Sincronizar ahora
          </Button>
        )}
        {conexion.conectada && esSuperAdmin && (
          <Button
            size="xs"
            variant="danger-ghost"
            leftIcon={<Unlink size={12} />}
            onClick={() => onDesconectar(conexion.plataforma)}
          >
            Desconectar
          </Button>
        )}
      </div>
    </div>
  )
}

export default function RedesSociales() {
  const { user } = useAuth()
  const socket = useSocket()
  const esSuperAdmin = user?.role === 'super_admin'
  const [conexiones, setConexiones] = useState([])
  const [cargando, setCargando] = useState(true)
  const [modalPlataforma, setModalPlataforma] = useState(null)
  const [sincronizando, setSincronizando] = useState(null)
  const [sincronizandoTodas, setSincronizandoTodas] = useState(false)

  function cargar() {
    conexionesApi
      .listarConexiones()
      .then(setConexiones)
      .catch(() => {})
      .finally(() => setCargando(false))
  }

  useEffect(() => {
    cargar()
  }, [])

  useEffect(() => {
    if (!socket) return undefined
    socket.on('conexion_social:actualizada', cargar)
    return () => socket.off('conexion_social:actualizada', cargar)
  }, [socket])

  async function sincronizar(plataforma) {
    setSincronizando(plataforma)
    try {
      const resultado = await conexionesApi.sincronizarConexion(plataforma)
      if (resultado.ok) {
        toast.success(`${nombrePlataforma(plataforma)} sincronizado correctamente`)
      } else {
        toast.error(resultado.error || 'No se pudo sincronizar')
      }
    } catch (err) {
      toast.error(err.response?.data?.error || 'No se pudo sincronizar')
    } finally {
      setSincronizando(null)
      cargar()
    }
  }

  async function sincronizarTodasLasConexiones() {
    setSincronizandoTodas(true)
    try {
      await conexionesApi.sincronizarTodas()
      toast.success('Sincronización enviada a todas las plataformas conectadas')
    } catch (err) {
      toast.error(err.response?.data?.error || 'No se pudo sincronizar')
    } finally {
      setSincronizandoTodas(false)
      cargar()
    }
  }

  async function desconectar(plataforma) {
    if (!window.confirm(`¿Quitar las credenciales de ${nombrePlataforma(plataforma)}? Dejará de sincronizarse automáticamente.`)) {
      return
    }
    await conexionesApi.eliminarConexion(plataforma)
    cargar()
  }

  const hayConectadas = conexiones.some((c) => c.conectada)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900 dark:text-white">Redes sociales</h1>
        <p className="mt-1 text-sm text-ink-500 dark:text-obsidian-muted">
          Conecta cada plataforma una sola vez; el sistema sincroniza las métricas solo, de forma periódica.
        </p>
      </div>

      <Card>
        <CardHeader
          title="Conexiones"
          description="Las credenciales quedan cifradas en el servidor y nunca se vuelven a mostrar."
          actions={
            hayConectadas && (
              <Button
                size="sm"
                variant="secondary"
                leftIcon={sincronizandoTodas ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                disabled={sincronizandoTodas}
                onClick={sincronizarTodasLasConexiones}
              >
                Sincronizar todas
              </Button>
            )
          }
        />
        {cargando && <p className="text-sm text-ink-500 dark:text-obsidian-muted">Cargando...</p>}
        {!cargando && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {conexiones.map((c) => (
              <TarjetaConexion
                key={c.plataforma}
                conexion={c}
                esSuperAdmin={esSuperAdmin}
                onConfigurar={setModalPlataforma}
                onSincronizar={sincronizar}
                onDesconectar={desconectar}
                sincronizando={sincronizando === c.plataforma}
              />
            ))}
          </div>
        )}
      </Card>

      {!esSuperAdmin && (
        <p className="text-xs text-ink-400 dark:text-obsidian-muted">
          Solo el súper administrador puede guardar o quitar credenciales; cualquier administrador puede sincronizar.
        </p>
      )}

      <ModalCredenciales
        open={Boolean(modalPlataforma)}
        onClose={() => setModalPlataforma(null)}
        plataforma={modalPlataforma}
        onGuardado={cargar}
      />
    </div>
  )
}
