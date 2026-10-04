import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Ban, Monitor, Plus, Share2, Trash2, TrendingUp, Wifi, WifiOff } from 'lucide-react'
import { Badge, Button, Card, CardHeader, Modal, StatCard } from '../components/ui'
import Input, { Label } from '../components/ui/Input'
import { actividadReciente } from '../api/auth'
import * as dashboardApi from '../api/dashboard'
import * as metricasApi from '../api/metricas'
import { useAuth } from '../context/AuthContext'
import { useSocket } from '../context/SocketContext'

function saludo() {
  const h = new Date().getHours()
  if (h < 12) return 'Buenos días'
  if (h < 19) return 'Buenas tardes'
  return 'Buenas noches'
}

function formatearNumero(n) {
  return new Intl.NumberFormat('es-MX').format(n || 0)
}

function formatearDuracion(segundos) {
  const s = segundos || 0
  const horas = Math.floor(s / 3600)
  const minutos = Math.floor((s % 3600) / 60)
  if (horas > 0) return `${horas} h ${minutos} min`
  if (minutos > 0) return `${minutos} min`
  return `${s} s`
}

function TarjetaMetrica({ metrica, onEditar, onEliminar }) {
  return (
    <div className="rounded-lg border border-ink-200 p-4 dark:border-obsidian-line">
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <p className="font-mono text-xs font-semibold uppercase tracking-wide text-ink-700 dark:text-ink-200">
            {metrica.red_social}
          </p>
          <Badge tone={metrica.origen === 'automatico' ? 'brand' : 'neutral'} className="whitespace-nowrap">
            {metrica.origen === 'automatico' ? 'Automático' : 'Manual'}
          </Badge>
        </div>
        <div className="flex gap-1">
          <button
            type="button"
            onClick={() => onEditar(metrica)}
            className="text-xs text-ink-400 hover:text-ink-700 dark:text-obsidian-muted dark:hover:text-white"
          >
            Editar
          </button>
          <button
            type="button"
            onClick={() => onEliminar(metrica)}
            className="text-ink-400 hover:text-red-600 dark:text-obsidian-muted dark:hover:text-red-400"
            aria-label="Quitar"
          >
            <Trash2 size={13} />
          </button>
        </div>
      </div>
      <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
        <div>
          <dt className="text-xs text-ink-500 dark:text-obsidian-muted">Me gusta</dt>
          <dd className="font-semibold text-ink-900 dark:text-white">{formatearNumero(metrica.me_gusta)}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-500 dark:text-obsidian-muted">Interacciones</dt>
          <dd className="font-semibold text-ink-900 dark:text-white">{formatearNumero(metrica.interacciones)}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-500 dark:text-obsidian-muted">Impresiones</dt>
          <dd className="font-semibold text-ink-900 dark:text-white">{formatearNumero(metrica.impresiones)}</dd>
        </div>
        <div>
          <dt className="text-xs text-ink-500 dark:text-obsidian-muted">Engagement</dt>
          <dd className="font-semibold text-ink-900 dark:text-white">{metrica.engagement}%</dd>
        </div>
      </dl>
    </div>
  )
}

function ModalMetrica({ open, onClose, onGuardado, metrica }) {
  const vacio = { red_social: '', me_gusta: 0, interacciones: 0, impresiones: 0, engagement: 0 }
  const [form, setForm] = useState(vacio)
  const [error, setError] = useState('')
  const [cargando, setCargando] = useState(false)

  useEffect(() => {
    setForm(metrica ? { ...metrica } : vacio)
    setError('')
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metrica, open])

  async function guardar(e) {
    e.preventDefault()
    setError('')
    setCargando(true)
    try {
      await metricasApi.guardarMetrica({
        red_social: form.red_social,
        me_gusta: Number(form.me_gusta) || 0,
        interacciones: Number(form.interacciones) || 0,
        impresiones: Number(form.impresiones) || 0,
        engagement: Number(form.engagement) || 0,
      })
      onGuardado()
      onClose()
    } catch (err) {
      setError(err.response?.data?.error || 'No se pudieron guardar las métricas')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Modal open={open} onClose={onClose} title={metrica ? `Editar ${metrica.red_social}` : 'Agregar red social'}>
      <form onSubmit={guardar} className="space-y-4">
        <div>
          <Label>Red social</Label>
          <Input
            value={form.red_social}
            onChange={(e) => setForm((f) => ({ ...f, red_social: e.target.value }))}
            placeholder="Instagram, Facebook, TikTok..."
            disabled={Boolean(metrica)}
            required
          />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <Label>Me gusta</Label>
            <Input type="number" min="0" value={form.me_gusta} onChange={(e) => setForm((f) => ({ ...f, me_gusta: e.target.value }))} />
          </div>
          <div>
            <Label>Interacciones</Label>
            <Input type="number" min="0" value={form.interacciones} onChange={(e) => setForm((f) => ({ ...f, interacciones: e.target.value }))} />
          </div>
          <div>
            <Label>Impresiones</Label>
            <Input type="number" min="0" value={form.impresiones} onChange={(e) => setForm((f) => ({ ...f, impresiones: e.target.value }))} />
          </div>
          <div>
            <Label>Engagement (%)</Label>
            <Input type="number" min="0" max="100" step="0.1" value={form.engagement} onChange={(e) => setForm((f) => ({ ...f, engagement: e.target.value }))} />
          </div>
        </div>
        {error && <div className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-950/40 dark:text-red-300">{error}</div>}
        <Button type="submit" className="w-full" loading={cargando}>
          Guardar
        </Button>
      </form>
    </Modal>
  )
}

export default function Inicio() {
  const { user } = useAuth()
  const socket = useSocket()
  const [actividad, setActividad] = useState([])
  const [cargandoActividad, setCargandoActividad] = useState(true)
  const [resumen, setResumen] = useState(null)
  const [metricas, setMetricas] = useState([])
  const [modalMetrica, setModalMetrica] = useState(null)
  const [mostrarModal, setMostrarModal] = useState(false)

  function cargarResumen() {
    dashboardApi.obtenerResumen().then(setResumen).catch(() => {})
  }

  function cargarMetricas() {
    metricasApi.listarMetricas().then(setMetricas).catch(() => {})
  }

  useEffect(() => {
    actividadReciente(8).then(setActividad).catch(() => {}).finally(() => setCargandoActividad(false))
    cargarResumen()
    cargarMetricas()
  }, [])

  useEffect(() => {
    if (!socket) return undefined
    const refrescar = () => cargarResumen()
    socket.on('equipo:alta', refrescar)
    socket.on('equipo:estado', refrescar)
    socket.on('equipo:politica_aplicada', refrescar)
    socket.on('equipo:uso', refrescar)
    socket.on('metrica:actualizada', cargarMetricas)
    return () => {
      socket.off('equipo:alta', refrescar)
      socket.off('equipo:estado', refrescar)
      socket.off('equipo:politica_aplicada', refrescar)
      socket.off('equipo:uso', refrescar)
      socket.off('metrica:actualizada', cargarMetricas)
    }
  }, [socket])

  async function eliminarMetrica(metrica) {
    if (!window.confirm(`¿Quitar "${metrica.red_social}" del resumen?`)) return
    await metricasApi.eliminarMetrica(metrica.id)
    cargarMetricas()
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900 dark:text-white">
          {saludo()}, {user?.full_name || user?.username}
        </h1>
        <p className="mt-1 text-sm text-ink-500 dark:text-obsidian-muted">Resumen general de la operación.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard label="Equipos registrados" value={resumen ? formatearNumero(resumen.equipos_registrados) : '—'} icon={Monitor} />
        <StatCard label="En línea" value={resumen ? formatearNumero(resumen.en_linea) : '—'} icon={Wifi} />
        <StatCard label="Fuera de línea" value={resumen ? formatearNumero(resumen.fuera_linea) : '—'} icon={WifiOff} />
        <StatCard label="Apps bloqueadas" value={resumen ? formatearNumero(resumen.apps_bloqueadas) : '—'} icon={Ban} />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader title="Actividad reciente" description="Tus últimas acciones en el panel." />
          {cargandoActividad && <p className="text-sm text-ink-500 dark:text-obsidian-muted">Cargando...</p>}
          {!cargandoActividad && actividad.length === 0 && (
            <p className="text-sm text-ink-500 dark:text-obsidian-muted">Todavía no hay actividad registrada.</p>
          )}
          <ul className="space-y-2">
            {actividad.map((item) => (
              <li key={item.id} className="flex items-center justify-between border-b border-ink-100 pb-2 text-sm last:border-0 last:pb-0 dark:border-obsidian-line">
                <span className="text-ink-700 dark:text-ink-200">{item.action}</span>
                <span className="text-xs text-ink-400 dark:text-obsidian-muted">
                  {item.created_at ? new Date(item.created_at).toLocaleString() : ''}
                </span>
              </li>
            ))}
          </ul>
        </Card>

        <Card>
          <CardHeader
            title="Aplicaciones más usadas"
            description="Últimos 7 días en todo el parque de equipos."
            actions={<TrendingUp size={16} className="text-ink-400 dark:text-obsidian-muted" />}
          />
          {!resumen && <p className="text-sm text-ink-500 dark:text-obsidian-muted">Cargando...</p>}
          {resumen && resumen.top_aplicaciones.length === 0 && (
            <p className="text-sm text-ink-500 dark:text-obsidian-muted">Todavía no hay uso de aplicaciones registrado.</p>
          )}
          <ul className="space-y-2">
            {resumen?.top_aplicaciones.map((app) => (
              <li key={app.ejecutable} className="flex items-center justify-between border-b border-ink-100 pb-2 text-sm last:border-0 last:pb-0 dark:border-obsidian-line">
                <div className="min-w-0">
                  <p className="truncate text-ink-700 dark:text-ink-200">{app.nombre}</p>
                  <p className="truncate font-mono text-[11px] text-ink-400 dark:text-obsidian-muted">{app.ejecutable}</p>
                </div>
                <Badge tone="neutral">{formatearDuracion(app.segundos)}</Badge>
              </li>
            ))}
          </ul>
        </Card>
      </div>

      <Card>
        <CardHeader
          title="Resumen de redes sociales"
          description="Métricas por plataforma: automáticas si está conectada, o capturadas a mano."
          actions={
            <div className="flex items-center gap-2">
              <Link to="/redes-sociales" className="text-xs font-medium text-brand-600 hover:underline dark:text-brand-300">
                Conectar plataformas
              </Link>
              <Button size="sm" leftIcon={<Plus size={14} />} onClick={() => { setModalMetrica(null); setMostrarModal(true) }}>
                Agregar
              </Button>
            </div>
          }
        />
        {metricas.length === 0 && (
          <div className="flex flex-col items-center gap-2 py-10 text-center">
            <Share2 size={22} className="text-ink-300 dark:text-obsidian-muted" />
            <p className="text-sm text-ink-500 dark:text-obsidian-muted">
              Todavía no hay métricas de redes sociales. Agrega una para empezar a llevar el control.
            </p>
          </div>
        )}
        {metricas.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {metricas.map((m) => (
              <TarjetaMetrica
                key={m.id}
                metrica={m}
                onEditar={(metrica) => { setModalMetrica(metrica); setMostrarModal(true) }}
                onEliminar={eliminarMetrica}
              />
            ))}
          </div>
        )}
      </Card>

      <ModalMetrica
        open={mostrarModal}
        onClose={() => setMostrarModal(false)}
        onGuardado={cargarMetricas}
        metrica={modalMetrica}
      />
    </div>
  )
}
