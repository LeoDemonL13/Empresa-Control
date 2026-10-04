import { useCallback, useEffect, useMemo, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { AlertTriangle, ExternalLink, Loader2, RefreshCw, Settings, Unlink } from 'lucide-react'
import toast from 'react-hot-toast'
import { Badge, Button, Card, CardHeader, Modal } from '../components/ui'
import * as redesApi from '../api/redesSociales'
import { useAuth } from '../context/AuthContext'
import { useSocket } from '../context/SocketContext'

const PLATAFORMAS = [
  { id: 'facebook', nombre: 'Facebook', color: 'bg-[#1877F2]' },
  { id: 'instagram', nombre: 'Instagram', color: 'bg-gradient-to-br from-[#F58529] via-[#DD2A7B] to-[#8134AF]' },
  { id: 'tiktok', nombre: 'TikTok', color: 'bg-ink-900' },
  { id: 'youtube', nombre: 'YouTube', color: 'bg-[#FF0000]' },
]

const RANGOS = [
  { id: '24h', etiqueta: '24 horas' },
  { id: '7d', etiqueta: '7 días' },
  { id: '30d', etiqueta: '30 días' },
]

function nombrePlataforma(id) {
  return PLATAFORMAS.find((p) => p.id === id)?.nombre || id
}

function formatearFecha(iso) {
  if (!iso) return 'Nunca'
  return new Date(iso).toLocaleString('es-MX')
}

function formatearNumero(valor) {
  if (valor === null || valor === undefined) return 'No disponible'
  return Number(valor).toLocaleString('es-MX')
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

function useMensajesDeRetorno() {
  const location = useLocation()
  const navigate = useNavigate()

  useEffect(() => {
    const params = new URLSearchParams(location.search)
    const conectado = params.get('conectado')
    const error = params.get('error')
    const advertencia = params.get('advertencia')

    if (conectado) {
      if (advertencia === 'primera_sincronizacion_fallo') {
        toast.error(
          `${nombrePlataforma(conectado)} se conectó, pero la primera sincronización falló. Revisa el panel de administración.`,
        )
      } else {
        toast.success(`${nombrePlataforma(conectado)} se conectó correctamente`)
      }
    } else if (error) {
      const plataforma = params.get('plataforma')
      const mensajes = {
        autorizacion_rechazada: 'Se rechazó la autorización en la plataforma',
        estado_invalido: 'La solicitud de conexión expiró o no es válida; intenta de nuevo',
        fallo_autorizacion: 'No se pudo completar la autorización con la plataforma',
        plataforma_no_soportada: 'Esa plataforma no está soportada',
      }
      toast.error(mensajes[error] || 'No se pudo completar la conexión', {
        id: `oauth-error-${plataforma || error}`,
      })
    }

    if (conectado || error) {
      navigate(location.pathname, { replace: true })
    }
  }, [location, navigate])
}

function PanelSistema({ estado }) {
  if (!estado) return null
  return (
    <Card className="bg-ink-50/60 dark:bg-obsidian-cardAlt/40">
      <div className="flex flex-wrap items-center gap-4 text-xs text-ink-600 dark:text-obsidian-muted">
        <span className="font-medium text-ink-900 dark:text-white">Monitor del sistema</span>
        <span>Intervalo de sincronización: cada {estado.intervalo_minutos} min</span>
        {estado.plataformas.map((p) => (
          <span key={p.plataforma} className="inline-flex items-center gap-1">
            {nombrePlataforma(p.plataforma)}:
            <span className="font-mono">
              {p.conectada ? (p.ultimo_resultado === 'ok' ? 'ok' : p.ultimo_resultado || 'pendiente') : 'sin conectar'}
            </span>
            {p.ultimo_tiempo_respuesta_ms != null && <span>({p.ultimo_tiempo_respuesta_ms} ms)</span>}
          </span>
        ))}
      </div>
    </Card>
  )
}

function PanelAdministracion({ plataforma, onClose, esSuperAdmin, onCambio }) {
  const [datos, setDatos] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [confirmarDesconexion, setConfirmarDesconexion] = useState(false)
  const [purgarHistorico, setPurgarHistorico] = useState(false)

  const cargar = useCallback(() => {
    setCargando(true)
    redesApi
      .obtenerSalud(plataforma)
      .then(setDatos)
      .finally(() => setCargando(false))
  }, [plataforma])

  useEffect(() => {
    cargar()
  }, [cargar])

  async function alternarSeguimiento(cuenta) {
    try {
      await redesApi.actualizarSeguimientoCuenta(plataforma, cuenta.id, !cuenta.seguimiento_activo)
      cargar()
      onCambio()
    } catch (err) {
      toast.error(err.response?.data?.error || 'No se pudo actualizar la cuenta')
    }
  }

  async function reconectar() {
    try {
      const { url } = await redesApi.obtenerUrlConexion(plataforma)
      window.location.href = url
    } catch (err) {
      toast.error(err.response?.data?.error || 'No se pudo iniciar la reconexión')
    }
  }

  async function desconectar() {
    try {
      await redesApi.desconectarConexion(plataforma, purgarHistorico)
      toast.success(`${nombrePlataforma(plataforma)} se desconectó`)
      setConfirmarDesconexion(false)
      onCambio()
      onClose()
    } catch (err) {
      toast.error(err.response?.data?.error || 'No se pudo desconectar')
    }
  }

  return (
    <Modal open onClose={onClose} title={`Administrar ${nombrePlataforma(plataforma)}`} className="max-w-lg">
      {cargando && <p className="text-sm text-ink-500 dark:text-obsidian-muted">Cargando...</p>}
      {!cargando && datos && (
        <div className="space-y-4">
          <div className="flex items-center gap-2">
            <span>{datos.icono}</span>
            <span className="font-medium text-ink-900 dark:text-white">{datos.estado_texto}</span>
          </div>

          {datos.cuenta_externa && (
            <p className="text-sm text-ink-600 dark:text-obsidian-muted">Cuenta autorizada: {datos.cuenta_externa}</p>
          )}
          {datos.alcance && (
            <p className="break-words text-xs text-ink-400 dark:text-obsidian-muted">Permisos: {datos.alcance}</p>
          )}

          <dl className="space-y-1 text-xs text-ink-500 dark:text-obsidian-muted">
            <div className="flex justify-between">
              <dt>Última sincronización</dt>
              <dd>{formatearFecha(datos.ultima_sincronizacion)}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Próxima sincronización</dt>
              <dd>{formatearFecha(datos.proxima_sincronizacion)}</dd>
            </div>
          </dl>

          {datos.ultimo_error && (
            <p className="rounded-md bg-red-50 px-2 py-1.5 text-xs text-red-700 dark:bg-red-950/40 dark:text-red-300">
              {datos.ultimo_error}
            </p>
          )}

          {datos.cuentas.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500 dark:text-obsidian-muted">
                Cuentas descubiertas
              </p>
              <ul className="space-y-2">
                {datos.cuentas.map((c) => (
                  <li key={c.id} className="flex items-center justify-between gap-2 text-sm">
                    <span className="truncate text-ink-800 dark:text-ink-200">{c.nombre}</span>
                    {esSuperAdmin ? (
                      <Button size="xs" variant={c.seguimiento_activo ? 'secondary' : 'ghost'} onClick={() => alternarSeguimiento(c)}>
                        {c.seguimiento_activo ? 'Siguiendo' : 'Pausado'}
                      </Button>
                    ) : (
                      <Badge tone={c.seguimiento_activo ? 'success' : 'neutral'}>
                        {c.seguimiento_activo ? 'Siguiendo' : 'Pausado'}
                      </Badge>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {datos.errores_recientes?.length > 0 && (
            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-ink-500 dark:text-obsidian-muted">
                Actividad reciente
              </p>
              <ul className="max-h-40 space-y-1 overflow-y-auto scrollbar-thin text-xs">
                {datos.errores_recientes.map((r, i) => (
                  <li
                    key={i}
                    className={r.estado === 'ok' ? 'text-ink-500 dark:text-obsidian-muted' : 'text-red-600 dark:text-red-300'}
                  >
                    {formatearFecha(r.iniciado_at)} · {r.disparado_por} · {r.estado === 'ok' ? 'correcto' : r.mensaje}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {esSuperAdmin && (
            <div className="flex flex-wrap gap-2 border-t border-ink-200 pt-4 dark:border-obsidian-line">
              <Button size="sm" variant="secondary" leftIcon={<ExternalLink size={14} />} onClick={reconectar}>
                Reconectar
              </Button>
              {!confirmarDesconexion ? (
                <Button size="sm" variant="danger-ghost" leftIcon={<Unlink size={14} />} onClick={() => setConfirmarDesconexion(true)}>
                  Desconectar
                </Button>
              ) : (
                <div className="w-full space-y-2 rounded-md bg-red-50 p-3 text-xs dark:bg-red-950/30">
                  <p className="text-red-700 dark:text-red-300">¿Quitar las credenciales de {nombrePlataforma(plataforma)}?</p>
                  <label className="flex items-center gap-2 text-ink-700 dark:text-ink-200">
                    <input
                      type="checkbox"
                      checked={purgarHistorico}
                      onChange={(e) => setPurgarHistorico(e.target.checked)}
                    />
                    Borrar también el histórico de métricas guardado
                  </label>
                  <div className="flex gap-2">
                    <Button size="xs" variant="danger" onClick={desconectar}>Confirmar</Button>
                    <Button size="xs" variant="ghost" onClick={() => setConfirmarDesconexion(false)}>Cancelar</Button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </Modal>
  )
}

function TarjetaConexion({ conexion, esSuperAdmin, onSincronizar, onAdministrar, sincronizando }) {
  return (
    <div className="rounded-lg border border-ink-200 p-4 dark:border-obsidian-line">
      <div className="flex items-center gap-3">
        <Insignia plataforma={conexion.plataforma} />
        <div className="min-w-0 flex-1">
          <p className="font-semibold text-ink-900 dark:text-white">{nombrePlataforma(conexion.plataforma)}</p>
          <p className="text-xs text-ink-500 dark:text-obsidian-muted">
            {conexion.icono} {conexion.estado_texto}
          </p>
        </div>
      </div>

      {conexion.cuenta_externa && (
        <p className="mt-2 truncate text-xs text-ink-500 dark:text-obsidian-muted">{conexion.cuenta_externa}</p>
      )}

      {conexion.conectada && (
        <dl className="mt-3 space-y-1 text-xs text-ink-500 dark:text-obsidian-muted">
          <div className="flex justify-between">
            <dt>Última sincronización</dt>
            <dd>{formatearFecha(conexion.ultima_sincronizacion)}</dd>
          </div>
          <div className="flex justify-between">
            <dt>Próxima sincronización</dt>
            <dd>{formatearFecha(conexion.proxima_sincronizacion)}</dd>
          </div>
        </dl>
      )}

      {conexion.ultimo_error && (
        <p className="mt-2 flex items-start gap-1.5 rounded-md bg-red-50 px-2 py-1.5 text-xs text-red-700 dark:bg-red-950/40 dark:text-red-300">
          <AlertTriangle size={12} className="mt-0.5 flex-shrink-0" />
          {conexion.ultimo_error}
        </p>
      )}

      {!conexion.configurada && (
        <p className="mt-3 text-xs text-ink-400 dark:text-obsidian-muted">
          Esta plataforma no tiene configuradas sus credenciales de aplicación en el servidor.
        </p>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {!conexion.conectada && conexion.configurada && esSuperAdmin && (
          <Button
            size="xs"
            variant="primary"
            leftIcon={<ExternalLink size={12} />}
            onClick={() => onAdministrar(conexion.plataforma, true)}
          >
            Conectar con {nombrePlataforma(conexion.plataforma)}
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
        {conexion.conectada && (
          <Button size="xs" variant="secondary" leftIcon={<Settings size={12} />} onClick={() => onAdministrar(conexion.plataforma, false)}>
            Administrar
          </Button>
        )}
      </div>
    </div>
  )
}

function PanelResumen({ esAdmin }) {
  const [rango, setRango] = useState('7d')
  const [resumen, setResumen] = useState(null)
  const [cargando, setCargando] = useState(false)

  const cargar = useCallback((nuevoRango) => {
    setCargando(true)
    redesApi
      .obtenerResumen({ rango: nuevoRango })
      .then(setResumen)
      .catch(() => setResumen(null))
      .finally(() => setCargando(false))
  }, [])

  useEffect(() => {
    if (esAdmin) cargar(rango)
  }, [cargar, rango, esAdmin])

  if (!esAdmin) return null

  return (
    <Card>
      <CardHeader
        title="Resumen de actividad"
        description="Generado a partir de los datos reales sincronizados"
        actions={
          <div className="flex gap-1">
            {RANGOS.map((r) => (
              <Button key={r.id} size="xs" variant={rango === r.id ? 'primary' : 'ghost'} onClick={() => setRango(r.id)}>
                {r.etiqueta}
              </Button>
            ))}
          </div>
        }
      />
      {cargando && <p className="text-sm text-ink-500 dark:text-obsidian-muted">Cargando...</p>}
      {!cargando && resumen && (
        <div className="space-y-4">
          <p className="text-sm text-ink-700 dark:text-ink-200">{resumen.narrativa}</p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="text-xs text-ink-500 dark:text-obsidian-muted">Publicaciones</p>
              <p className="text-lg font-semibold text-ink-900 dark:text-white">{formatearNumero(resumen.publicaciones)}</p>
            </div>
            <div>
              <p className="text-xs text-ink-500 dark:text-obsidian-muted">Interacciones</p>
              <p className="text-lg font-semibold text-ink-900 dark:text-white">{formatearNumero(resumen.interacciones)}</p>
            </div>
            <div>
              <p className="text-xs text-ink-500 dark:text-obsidian-muted">Impresiones</p>
              <p className="text-lg font-semibold text-ink-900 dark:text-white">{formatearNumero(resumen.impresiones)}</p>
            </div>
            <div>
              <p className="text-xs text-ink-500 dark:text-obsidian-muted">Engagement promedio</p>
              <p className="text-lg font-semibold text-ink-900 dark:text-white">
                {resumen.tasa_engagement_promedio != null ? `${resumen.tasa_engagement_promedio}%` : 'No disponible'}
              </p>
            </div>
          </div>

          {resumen.por_cuenta?.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="text-ink-500 dark:text-obsidian-muted">
                  <tr>
                    <th className="py-1 pr-4">Cuenta</th>
                    <th className="py-1 pr-4">Publicaciones</th>
                    <th className="py-1 pr-4">Me gusta</th>
                    <th className="py-1 pr-4">Comentarios</th>
                    <th className="py-1 pr-4">Engagement</th>
                  </tr>
                </thead>
                <tbody className="text-ink-800 dark:text-ink-200">
                  {resumen.por_cuenta.map((c, i) => (
                    <tr key={i} className="border-t border-ink-100 dark:border-obsidian-line">
                      <td className="py-1.5 pr-4">{nombrePlataforma(c.plataforma)} · {c.cuenta}</td>
                      <td className="py-1.5 pr-4">{c.publicaciones}</td>
                      <td className="py-1.5 pr-4">{formatearNumero(c.me_gusta)}</td>
                      <td className="py-1.5 pr-4">{formatearNumero(c.comentarios)}</td>
                      <td className="py-1.5 pr-4">
                        {c.tasa_engagement_promedio != null ? `${c.tasa_engagement_promedio}%` : 'No disponible'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </Card>
  )
}

export default function RedesSociales() {
  const { user } = useAuth()
  const socket = useSocket()
  const esSuperAdmin = user?.role === 'super_admin'
  const esAdmin = user?.role === 'super_admin' || user?.role === 'admin'

  const [conexiones, setConexiones] = useState([])
  const [cargando, setCargando] = useState(true)
  const [sincronizando, setSincronizando] = useState(null)
  const [sincronizandoTodas, setSincronizandoTodas] = useState(false)
  const [plataformaAdministrar, setPlataformaAdministrar] = useState(null)
  const [estadoSistema, setEstadoSistema] = useState(null)

  useMensajesDeRetorno()

  const cargar = useCallback(() => {
    redesApi
      .listarConexiones()
      .then(setConexiones)
      .catch(() => {})
      .finally(() => setCargando(false))
  }, [])

  const cargarSistema = useCallback(() => {
    redesApi.obtenerEstadoSistema().then(setEstadoSistema).catch(() => {})
  }, [])

  useEffect(() => {
    cargar()
    cargarSistema()
  }, [cargar, cargarSistema])

  useEffect(() => {
    if (!socket) return undefined
    const manejar = () => {
      cargar()
      cargarSistema()
    }
    socket.on('conexion_social:actualizada', manejar)
    return () => socket.off('conexion_social:actualizada', manejar)
  }, [socket, cargar, cargarSistema])

  async function sincronizar(plataforma) {
    setSincronizando(plataforma)
    try {
      const resultado = await redesApi.sincronizarConexion(plataforma)
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
      await redesApi.sincronizarTodas()
      toast.success('Sincronización enviada a todas las plataformas conectadas')
    } catch (err) {
      toast.error(err.response?.data?.error || 'No se pudo sincronizar')
    } finally {
      setSincronizandoTodas(false)
      cargar()
    }
  }

  async function administrarOConectar(plataforma, esConectar) {
    if (esConectar) {
      try {
        const { url } = await redesApi.obtenerUrlConexion(plataforma)
        window.location.href = url
      } catch (err) {
        toast.error(err.response?.data?.error || 'No se pudo iniciar la conexión')
      }
      return
    }
    setPlataformaAdministrar(plataforma)
  }

  const hayConectadas = useMemo(() => conexiones.some((c) => c.conectada), [conexiones])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900 dark:text-white">Redes sociales</h1>
        <p className="mt-1 text-sm text-ink-500 dark:text-obsidian-muted">
          Conecta cada plataforma con su inicio de sesión oficial; el sistema sincroniza las métricas solo, de forma periódica.
        </p>
      </div>

      <PanelSistema estado={estadoSistema} />

      <Card>
        <CardHeader
          title="Conexiones"
          description="Cada conexión se autoriza con el inicio de sesión real de la plataforma."
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
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {conexiones.map((c) => (
              <TarjetaConexion
                key={c.plataforma}
                conexion={c}
                esSuperAdmin={esSuperAdmin}
                onSincronizar={sincronizar}
                onAdministrar={administrarOConectar}
                sincronizando={sincronizando === c.plataforma}
              />
            ))}
          </div>
        )}
      </Card>

      {!esSuperAdmin && (
        <p className="text-xs text-ink-400 dark:text-obsidian-muted">
          Solo el súper administrador puede conectar, reconectar o desconectar plataformas; cualquier administrador puede sincronizar.
        </p>
      )}

      <PanelResumen esAdmin={esAdmin} />

      {plataformaAdministrar && (
        <PanelAdministracion
          plataforma={plataformaAdministrar}
          esSuperAdmin={esSuperAdmin}
          onClose={() => setPlataformaAdministrar(null)}
          onCambio={cargar}
        />
      )}
    </div>
  )
}
