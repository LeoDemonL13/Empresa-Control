import { useEffect, useMemo, useState } from 'react'
import {
  AppWindow, Ban, KeyRound, Monitor, Network, Plus, RefreshCw, ShieldBan, ShieldCheck,
  Smartphone, Trash2, User, Wifi, WifiOff,
} from 'lucide-react'
import { Badge, Button, Card, Modal } from '../components/ui'
import Input, { Label } from '../components/ui/Input'
import Select from '../components/ui/Select'
import * as equiposApi from '../api/equipos'
import * as categoriasApi from '../api/categorias'
import { useSocket } from '../context/SocketContext'

function Alerta({ children }) {
  if (!children) return null
  return <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">{children}</div>
}

const ICONO_TIPO = { pc: Monitor, android: Smartphone }
const ETIQUETA_TIPO = { pc: 'PC', android: 'Android' }

function formatearDuracion(segundos) {
  const s = segundos || 0
  const horas = Math.floor(s / 3600)
  const minutos = Math.floor((s % 3600) / 60)
  if (horas > 0) return `${horas} h ${minutos} min`
  if (minutos > 0) return `${minutos} min`
  return `${s} s`
}

function FilaAplicacion({ equipoId, politica, maxUso7dias, onCambiado }) {
  const [tipoUso, setTipoUso] = useState(politica.tipo_uso)
  const [minutos, setMinutos] = useState(politica.limite_minutos || '')
  const [error, setError] = useState('')

  async function cambiarEstado(estado) {
    setError('')
    try {
      await equiposApi.actualizarPolitica(equipoId, politica.aplicacion.id, { estado })
      onCambiado()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo actualizar la política')
    }
  }

  async function guardarTipoUso() {
    setError('')
    const payload = { tipo_uso: tipoUso }
    if (tipoUso === 'con_limite') payload.limite_minutos = Number(minutos) || 0
    try {
      await equiposApi.actualizarPolitica(equipoId, politica.aplicacion.id, payload)
      onCambiado()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo actualizar la política')
    }
  }

  async function quitar() {
    if (!window.confirm(`¿Quitar "${politica.aplicacion.nombre}" de este equipo?`)) return
    await equiposApi.quitarAplicacion(equipoId, politica.aplicacion.id)
    onCambiado()
  }

  const porcentajeUso = maxUso7dias > 0 ? Math.round((politica.uso_7dias_segundos / maxUso7dias) * 100) : 0

  return (
    <div className="space-y-2 border-b border-ink-200 py-3 last:border-0 dark:border-obsidian-line">
      <div className="flex items-center justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-ink-900 dark:text-white">{politica.aplicacion.nombre}</p>
          <p className="truncate font-mono text-[11px] text-ink-500 dark:text-obsidian-muted">{politica.aplicacion.ejecutable}</p>
        </div>
        <div className="flex flex-shrink-0 items-center gap-1.5">
          <Button
            size="xs"
            variant={politica.estado === 'permitida' ? 'success' : 'secondary'}
            leftIcon={<ShieldCheck size={13} />}
            onClick={() => cambiarEstado('permitida')}
          >
            Permitida
          </Button>
          <Button
            size="xs"
            variant={politica.estado === 'bloqueada' ? 'danger' : 'secondary'}
            leftIcon={<ShieldBan size={13} />}
            onClick={() => cambiarEstado('bloqueada')}
          >
            Bloqueada
          </Button>
          <Button size="icon-sm" variant="danger-ghost" onClick={quitar} aria-label="Quitar">
            <Trash2 size={14} />
          </Button>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Select value={tipoUso} onChange={(e) => setTipoUso(e.target.value)} className="h-8 w-40 text-xs">
          <option value="sin_limite">Sin límite</option>
          <option value="con_limite">Con límite</option>
        </Select>
        {tipoUso === 'con_limite' && (
          <Input
            type="number"
            min="1"
            value={minutos}
            onChange={(e) => setMinutos(e.target.value)}
            placeholder="Minutos/día"
            className="h-8 w-28 text-xs"
          />
        )}
        {(tipoUso !== politica.tipo_uso || (tipoUso === 'con_limite' && Number(minutos) !== politica.limite_minutos)) && (
          <Button size="xs" variant="secondary" onClick={guardarTipoUso}>
            Guardar
          </Button>
        )}
      </div>

      <div className="space-y-1">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-100 dark:bg-white/5">
          <div className="h-full rounded-full bg-accent" style={{ width: `${porcentajeUso}%` }} />
        </div>
        <p className="text-[11px] text-ink-500 dark:text-obsidian-muted">
          Hoy: {formatearDuracion(politica.uso_hoy_segundos)} · Últimos 7 días: {formatearDuracion(politica.uso_7dias_segundos)}
        </p>
      </div>

      <Alerta>{error}</Alerta>
    </div>
  )
}

function PanelAplicaciones({ equipoId, tipo }) {
  const [politicas, setPoliticas] = useState(null)
  const [ejecutable, setEjecutable] = useState('')
  const [appsInstaladas, setAppsInstaladas] = useState([])
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  function cargar() {
    equiposApi.listarAplicaciones(equipoId).then(setPoliticas).catch(() => {})
  }

  useEffect(cargar, [equipoId])

  useEffect(() => {
    if (tipo !== 'android') return
    equiposApi.listarAppsInstaladas(equipoId).then(setAppsInstaladas).catch(() => {})
  }, [equipoId, tipo])

  async function agregar(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const paquete = ejecutable.trim()
      const coincidencia = appsInstaladas.find((a) => a.paquete === paquete)
      const payload = coincidencia ? { ejecutable: paquete, nombre: coincidencia.etiqueta } : { ejecutable: paquete }
      await equiposApi.agregarAplicacion(equipoId, payload)
      setEjecutable('')
      cargar()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo agregar la aplicación')
    } finally {
      setCargando(false)
    }
  }

  const maxUso7dias = useMemo(
    () => Math.max(1, ...(politicas || []).map((p) => p.uso_7dias_segundos || 0)),
    [politicas],
  )

  const listaId = `lista-apps-instaladas-${equipoId}`

  return (
    <div className="space-y-4">
      <form onSubmit={agregar} className="flex items-end gap-2">
        <div className="flex-1">
          <Label>{tipo === 'android' ? 'Agregar aplicación por paquete' : 'Agregar aplicación por ejecutable'}</Label>
          <Input
            value={ejecutable}
            onChange={(e) => setEjecutable(e.target.value)}
            placeholder={tipo === 'android' ? 'com.instagram.android' : 'discord.exe'}
            list={tipo === 'android' ? listaId : undefined}
            required
          />
          {tipo === 'android' && (
            <datalist id={listaId}>
              {appsInstaladas.map((a) => (
                <option key={a.paquete} value={a.paquete}>
                  {a.etiqueta}
                </option>
              ))}
            </datalist>
          )}
        </div>
        <Button type="submit" leftIcon={<Plus size={14} />} loading={cargando}>
          Agregar
        </Button>
      </form>
      {tipo === 'android' && appsInstaladas.length === 0 && (
        <p className="text-xs text-ink-400 dark:text-obsidian-muted">
          Todavía no hay apps sincronizadas desde el teléfono; puedes escribir el paquete a mano mientras tanto.
        </p>
      )}
      <Alerta>{error}</Alerta>

      {politicas === null && <p className="text-sm text-ink-500 dark:text-obsidian-muted">Cargando...</p>}
      {politicas && politicas.length === 0 && (
        <p className="text-sm text-ink-500 dark:text-obsidian-muted">Este equipo no tiene aplicaciones en su matriz de control todavía.</p>
      )}
      {politicas && politicas.length > 0 && (
        <div>
          {politicas.map((p) => (
            <FilaAplicacion key={p.id} equipoId={equipoId} politica={p} maxUso7dias={maxUso7dias} onCambiado={cargar} />
          ))}
        </div>
      )}
    </div>
  )
}

function CampoCategoria({ value, onChange, categorias }) {
  return (
    <div>
      <Label>Categoría</Label>
      <Input
        list="lista-categorias"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Ventas, Bodega, Gerencia..."
      />
      <datalist id="lista-categorias">
        {categorias.map((c) => (
          <option key={c.id} value={c.nombre} />
        ))}
      </datalist>
      <p className="mt-1 text-xs text-ink-400 dark:text-obsidian-muted">
        Si escribes una categoría nueva, se crea automáticamente.
      </p>
    </div>
  )
}

function EquipoCard({ equipo, onVer }) {
  const IconoTipo = ICONO_TIPO[equipo.tipo] || Monitor
  return (
    <Card padded={false} className="flex flex-col">
      <div className="flex items-start justify-between gap-3 p-5 pb-4">
        <div className="flex min-w-0 items-center gap-3">
          <div className="inline-flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-lg bg-ink-100 text-ink-700 dark:bg-obsidian-cardAlt dark:text-ink-200">
            <IconoTipo size={22} strokeWidth={1.8} />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-ink-900 dark:text-white">{equipo.nombre}</p>
            <p className="mt-0.5 flex items-center gap-1 truncate text-xs text-ink-500 dark:text-obsidian-muted">
              <User size={12} /> {equipo.usuario_asignado || 'Sin usuario asignado'}
            </p>
          </div>
        </div>
        {equipo.en_linea ? (
          <Badge tone="success" dot mono leftIcon={<Wifi size={12} />}>
            En línea
          </Badge>
        ) : (
          <Badge tone="neutral" mono leftIcon={<WifiOff size={12} />}>
            Fuera de línea
          </Badge>
        )}
      </div>
      <div className="space-y-2 border-t border-ink-200 px-5 py-3 dark:border-obsidian-line">
        <p className="flex items-center gap-2 font-mono text-[11px] text-ink-500 dark:text-obsidian-muted">
          <Network size={13} />
          {[equipo.ip, equipo.mac, equipo.hostname].filter(Boolean).join(' · ') || 'Sin datos de red todavía'}
        </p>
        <p className="flex items-center gap-2 text-xs text-ink-500 dark:text-obsidian-muted">
          <AppWindow size={13} /> {equipo.enrolado ? `Agente v${equipo.agente_version || '—'}` : 'Agente no enrolado'}
        </p>
      </div>
      <div className="flex items-center justify-between gap-2 border-t border-ink-200 px-5 py-3 dark:border-obsidian-line">
        <div className="flex items-center gap-1.5">
          <Badge tone="neutral" mono>{ETIQUETA_TIPO[equipo.tipo] || 'PC'}</Badge>
          <Badge tone="neutral">{equipo.categoria?.nombre || 'Sin categoría'}</Badge>
        </div>
        <Button size="sm" variant="secondary" onClick={() => onVer(equipo.id)}>
          Ver
        </Button>
      </div>
    </Card>
  )
}

const FORM_VACIO_CREAR = { nombre: '', tipo: 'pc', usuario_asignado: '', categoria: '' }

function ModalCrear({ open, onClose, onCreado, categorias }) {
  const [form, setForm] = useState(FORM_VACIO_CREAR)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)
  const [creado, setCreado] = useState(null)

  function cerrar() {
    setForm(FORM_VACIO_CREAR)
    setCreado(null)
    setError('')
    onClose()
  }

  async function crear(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const data = await equiposApi.crearEquipo(form)
      setCreado(data)
      onCreado()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo crear el equipo')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Modal open={open} onClose={cerrar} title={creado ? 'Código de enrolamiento' : 'Nuevo equipo'}>
      {!creado && (
        <form onSubmit={crear} className="space-y-4">
          <div>
            <Label>Nombre del equipo</Label>
            <Input
              value={form.nombre}
              onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))}
              placeholder={form.tipo === 'android' ? 'Telefono-Ventas' : 'PC-Recepcion'}
              required
            />
          </div>
          <div>
            <Label>Tipo de equipo</Label>
            <Select aria-label="Tipo de equipo" value={form.tipo} onChange={(e) => setForm((f) => ({ ...f, tipo: e.target.value }))}>
              <option value="pc">PC (Windows)</option>
              <option value="android">Celular o tablet Android</option>
            </Select>
          </div>
          <div>
            <Label>Usuario asignado</Label>
            <Input value={form.usuario_asignado} onChange={(e) => setForm((f) => ({ ...f, usuario_asignado: e.target.value }))} />
          </div>
          <CampoCategoria value={form.categoria} onChange={(v) => setForm((f) => ({ ...f, categoria: v }))} categorias={categorias} />
          <p className="text-xs text-ink-500 dark:text-obsidian-muted">
            Hostname, IP y sistema operativo no se piden aquí: se completan solos en cuanto el agente se enrola con el código.
          </p>
          <Alerta>{error}</Alerta>
          <Button type="submit" className="w-full" loading={cargando}>
            Crear equipo
          </Button>
        </form>
      )}

      {creado && (
        <div className="space-y-4">
          <div className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
            Equipo creado. Usa este código en el instalador del agente, se muestra una sola vez.
          </div>
          <p className="text-center font-mono text-2xl font-semibold tracking-widest text-ink-900 dark:text-white">
            {creado.codigo_enrolamiento}
          </p>
          <p className="text-center text-xs text-ink-500 dark:text-obsidian-muted">
            Expira: {new Date(creado.codigo_expira_at).toLocaleString()}
          </p>
          <Button className="w-full" onClick={cerrar}>
            Listo
          </Button>
        </div>
      )}
    </Modal>
  )
}

function ModalVer({ equipoId, onClose, onCambiado, categorias }) {
  const [equipo, setEquipo] = useState(null)
  const [editando, setEditando] = useState(false)
  const [form, setForm] = useState(null)
  const [codigo, setCodigo] = useState(null)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)
  const [pestana, setPestana] = useState('info')

  useEffect(() => {
    if (!equipoId) {
      setEquipo(null)
      setEditando(false)
      setCodigo(null)
      setPestana('info')
      return
    }
    equiposApi.obtenerEquipo(equipoId).then((data) => {
      setEquipo(data)
      setForm({
        nombre: data.nombre,
        tipo: data.tipo || 'pc',
        usuario_asignado: data.usuario_asignado || '',
        categoria: data.categoria?.nombre || '',
      })
    })
  }, [equipoId])

  async function guardar(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      const actualizado = await equiposApi.actualizarEquipo(equipoId, form)
      setEquipo(actualizado)
      setEditando(false)
      onCambiado()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo actualizar el equipo')
    } finally {
      setCargando(false)
    }
  }

  async function regenerar() {
    setError('')
    try {
      const data = await equiposApi.regenerarEnrolamiento(equipoId)
      setCodigo(data)
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudo generar el código')
    }
  }

  async function darDeBaja() {
    if (!window.confirm(`¿Dar de baja "${equipo.nombre}"?`)) return
    await equiposApi.eliminarEquipo(equipoId)
    onCambiado()
    onClose()
  }

  return (
    <Modal open={Boolean(equipoId)} onClose={onClose} title={equipo?.nombre || 'Equipo'} className="max-w-2xl">
      {!equipo && <p className="text-sm text-ink-500 dark:text-obsidian-muted">Cargando...</p>}

      {equipo && !editando && (
        <div className="space-y-4">
          <div className="flex gap-1 border-b border-ink-200 dark:border-obsidian-line">
            <button
              type="button"
              onClick={() => setPestana('info')}
              className={`px-3 py-2 text-sm font-medium ${pestana === 'info' ? 'border-b-2 border-accent text-ink-900 dark:text-white' : 'text-ink-500 dark:text-obsidian-muted'}`}
            >
              Información
            </button>
            <button
              type="button"
              onClick={() => setPestana('aplicaciones')}
              className={`px-3 py-2 text-sm font-medium ${pestana === 'aplicaciones' ? 'border-b-2 border-accent text-ink-900 dark:text-white' : 'text-ink-500 dark:text-obsidian-muted'}`}
            >
              Aplicaciones
            </button>
          </div>

          {pestana === 'aplicaciones' && <PanelAplicaciones equipoId={equipo.id} tipo={equipo.tipo} />}

          {pestana === 'info' && (
            <>
          <div className="flex items-center gap-2">
            {equipo.en_linea ? (
              <Badge tone="success" dot mono leftIcon={<Wifi size={12} />}>En línea</Badge>
            ) : (
              <Badge tone="neutral" mono leftIcon={<WifiOff size={12} />}>Fuera de línea</Badge>
            )}
            <Badge tone="neutral" mono>{ETIQUETA_TIPO[equipo.tipo] || 'PC'}</Badge>
            <Badge tone="neutral">{equipo.categoria?.nombre || 'Sin categoría'}</Badge>
          </div>

          <dl className="grid grid-cols-2 gap-3 text-sm">
            <div>
              <dt className="text-xs text-ink-500 dark:text-obsidian-muted">Usuario</dt>
              <dd className="text-ink-800 dark:text-ink-200">{equipo.usuario_asignado || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-500 dark:text-obsidian-muted">Sistema operativo</dt>
              <dd className="text-ink-800 dark:text-ink-200">{equipo.sistema_operativo || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-500 dark:text-obsidian-muted">IP</dt>
              <dd className="font-mono text-ink-800 dark:text-ink-200">{equipo.ip || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-500 dark:text-obsidian-muted">Hostname</dt>
              <dd className="font-mono text-ink-800 dark:text-ink-200">{equipo.hostname || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-500 dark:text-obsidian-muted">MAC</dt>
              <dd className="font-mono text-ink-800 dark:text-ink-200">{equipo.mac || '—'}</dd>
            </div>
            <div>
              <dt className="text-xs text-ink-500 dark:text-obsidian-muted">Agente</dt>
              <dd className="text-ink-800 dark:text-ink-200">{equipo.enrolado ? `v${equipo.agente_version || '—'}` : 'No enrolado'}</dd>
            </div>
          </dl>

          <div className="rounded-md border border-ink-200 p-3 dark:border-obsidian-line">
            {codigo ? (
              <div className="space-y-1 text-center">
                <p className="font-mono text-xl font-semibold tracking-widest text-ink-900 dark:text-white">
                  {codigo.codigo_enrolamiento}
                </p>
                <p className="text-xs text-ink-500 dark:text-obsidian-muted">
                  Expira: {new Date(codigo.codigo_expira_at).toLocaleString()}
                </p>
              </div>
            ) : equipo.codigo_pendiente ? (
              <div className="flex items-center justify-between text-sm">
                <span className="text-ink-600 dark:text-ink-300">
                  Hay un código sin usar, vence {new Date(equipo.codigo_pendiente.expira_at).toLocaleString()}
                </span>
                <Button size="xs" variant="secondary" leftIcon={<RefreshCw size={13} />} onClick={regenerar}>
                  Regenerar
                </Button>
              </div>
            ) : (
              <div className="flex items-center justify-between text-sm">
                <span className="text-ink-500 dark:text-obsidian-muted">Sin código de enrolamiento activo</span>
                <Button size="xs" variant="secondary" leftIcon={<KeyRound size={13} />} onClick={regenerar}>
                  Generar código
                </Button>
              </div>
            )}
          </div>

          <Alerta>{error}</Alerta>

          <div className="flex justify-between">
            <Button variant="danger-ghost" leftIcon={<Trash2 size={14} />} onClick={darDeBaja}>
              Dar de baja
            </Button>
            <Button variant="secondary" onClick={() => setEditando(true)}>
              Editar
            </Button>
          </div>
            </>
          )}
        </div>
      )}

      {equipo && editando && form && (
        <form onSubmit={guardar} className="space-y-4">
          <div>
            <Label>Nombre</Label>
            <Input value={form.nombre} onChange={(e) => setForm((f) => ({ ...f, nombre: e.target.value }))} required />
          </div>
          <div>
            <Label>Tipo de equipo</Label>
            <Select aria-label="Tipo de equipo" value={form.tipo} onChange={(e) => setForm((f) => ({ ...f, tipo: e.target.value }))}>
              <option value="pc">PC (Windows)</option>
              <option value="android">Celular o tablet Android</option>
            </Select>
          </div>
          <div>
            <Label>Usuario asignado</Label>
            <Input value={form.usuario_asignado} onChange={(e) => setForm((f) => ({ ...f, usuario_asignado: e.target.value }))} />
          </div>
          <CampoCategoria value={form.categoria} onChange={(v) => setForm((f) => ({ ...f, categoria: v }))} categorias={categorias} />
          <p className="text-xs text-ink-500 dark:text-obsidian-muted">
            Hostname, IP y sistema operativo los reporta el agente solo; se ven en la pestaña "Información".
          </p>
          <Alerta>{error}</Alerta>
          <div className="flex gap-2">
            <Button type="button" variant="secondary" className="w-full" onClick={() => setEditando(false)}>
              Cancelar
            </Button>
            <Button type="submit" className="w-full" loading={cargando}>
              Guardar
            </Button>
          </div>
        </form>
      )}
    </Modal>
  )
}

export default function Equipos() {
  const [equipos, setEquipos] = useState([])
  const [categorias, setCategorias] = useState([])
  const [cargando, setCargando] = useState(true)
  const [filtros, setFiltros] = useState({ categoria_id: '', estado: '', q: '' })
  const [modalCrear, setModalCrear] = useState(false)
  const [verId, setVerId] = useState(null)
  const socket = useSocket()

  function cargarCategorias() {
    categoriasApi.listarCategorias().then(setCategorias).catch(() => {})
  }

  function cargarEquipos() {
    setCargando(true)
    const params = {}
    if (filtros.categoria_id) params.categoria_id = filtros.categoria_id
    if (filtros.estado) params.estado = filtros.estado
    if (filtros.q) params.q = filtros.q
    equiposApi
      .listarEquipos(params)
      .then(setEquipos)
      .finally(() => setCargando(false))
  }

  useEffect(cargarCategorias, [])
  useEffect(cargarEquipos, [filtros.categoria_id, filtros.estado, filtros.q])

  useEffect(() => {
    if (!socket) return undefined
    const refrescar = () => {
      cargarEquipos()
      cargarCategorias()
    }
    socket.on('equipo:alta', refrescar)
    socket.on('equipo:estado', refrescar)
    socket.on('categoria:nueva', cargarCategorias)
    return () => {
      socket.off('equipo:alta', refrescar)
      socket.off('equipo:estado', refrescar)
      socket.off('categoria:nueva', cargarCategorias)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [socket, filtros.categoria_id, filtros.estado, filtros.q])

  const sinResultados = useMemo(() => !cargando && equipos.length === 0, [cargando, equipos])

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-ink-900 dark:text-white">Equipos</h1>
          <p className="mt-1 text-sm text-ink-500 dark:text-obsidian-muted">Alta, categorías y estado de conexión.</p>
        </div>
        <Button leftIcon={<Plus size={16} />} onClick={() => setModalCrear(true)}>
          Agregar equipo
        </Button>
      </div>

      <Card>
        <div className="grid gap-3 sm:grid-cols-3">
          <Input placeholder="Buscar por nombre o usuario" value={filtros.q} onChange={(e) => setFiltros((f) => ({ ...f, q: e.target.value }))} />
          <Select value={filtros.categoria_id} onChange={(e) => setFiltros((f) => ({ ...f, categoria_id: e.target.value }))}>
            <option value="">Todas las categorías</option>
            {categorias.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre} ({c.total_equipos})
              </option>
            ))}
          </Select>
          <Select value={filtros.estado} onChange={(e) => setFiltros((f) => ({ ...f, estado: e.target.value }))}>
            <option value="">Cualquier estado</option>
            <option value="en_linea">En línea</option>
            <option value="fuera_linea">Fuera de línea</option>
          </Select>
        </div>
      </Card>

      {cargando && <p className="text-sm text-ink-500 dark:text-obsidian-muted">Cargando...</p>}

      {sinResultados && (
        <Card className="flex flex-col items-center gap-2 py-16 text-center">
          <Ban size={24} className="text-ink-300 dark:text-obsidian-muted" />
          <p className="text-sm text-ink-500 dark:text-obsidian-muted">No hay equipos con estos filtros.</p>
        </Card>
      )}

      {!cargando && equipos.length > 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {equipos.map((equipo) => (
            <EquipoCard key={equipo.id} equipo={equipo} onVer={setVerId} />
          ))}
        </div>
      )}

      <ModalCrear
        open={modalCrear}
        onClose={() => setModalCrear(false)}
        onCreado={() => {
          cargarEquipos()
          cargarCategorias()
        }}
        categorias={categorias}
      />
      <ModalVer
        equipoId={verId}
        onClose={() => setVerId(null)}
        onCambiado={() => {
          cargarEquipos()
          cargarCategorias()
        }}
        categorias={categorias}
      />
    </div>
  )
}
