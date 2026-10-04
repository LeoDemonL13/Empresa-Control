import { useEffect, useState } from 'react'
import { Download, FileSpreadsheet, FileText, ShieldCheck } from 'lucide-react'
import { Button, Card, CardHeader } from '../components/ui'
import Input, { Label } from '../components/ui/Input'
import Select from '../components/ui/Select'
import * as categoriasApi from '../api/categorias'
import * as equiposApi from '../api/equipos'
import * as reportesApi from '../api/reportes'

const FORMATOS = [
  { value: 'pdf', label: 'PDF' },
  { value: 'csv', label: 'CSV' },
  { value: 'xlsx', label: 'Excel' },
]

const ORIGENES = [
  { value: '', label: 'Todos los orígenes' },
  { value: 'panel', label: 'Panel' },
  { value: 'agente', label: 'Agente' },
  { value: 'sistema', label: 'Sistema' },
]

function fechaISO(fecha) {
  const mes = String(fecha.getMonth() + 1).padStart(2, '0')
  const dia = String(fecha.getDate()).padStart(2, '0')
  return `${fecha.getFullYear()}-${mes}-${dia}`
}

function hoyISO() {
  return fechaISO(new Date())
}

function haceDiasISO(dias) {
  const fecha = new Date()
  fecha.setDate(fecha.getDate() - dias)
  return fechaISO(fecha)
}

function SelectorFormato({ value, onChange, etiqueta = 'Formato' }) {
  return (
    <div>
      <Label>Formato</Label>
      <Select aria-label={etiqueta} value={value} onChange={(e) => onChange(e.target.value)}>
        {FORMATOS.map((f) => (
          <option key={f.value} value={f.value}>
            {f.label}
          </option>
        ))}
      </Select>
    </div>
  )
}

function ReporteGeneral() {
  const [formato, setFormato] = useState('pdf')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  async function descargar() {
    setError('')
    setCargando(true)
    try {
      await reportesApi.descargarReporteGeneral(formato)
    } catch (err) {
      setError((await reportesApi.extraerErrorDeBlob(err)) || 'No se pudo generar el reporte')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Card>
      <CardHeader
        title="Reporte general"
        description="Inventario completo de equipos: categoría, usuario asignado, IP, estado del agente y fecha de alta."
        actions={<FileText size={18} className="text-ink-400 dark:text-obsidian-muted" />}
      />
      <div className="flex flex-wrap items-end gap-3">
        <div className="w-40">
          <SelectorFormato value={formato} onChange={setFormato} etiqueta="Formato del reporte general" />
        </div>
        <Button leftIcon={<Download size={15} />} loading={cargando} onClick={descargar}>
          Descargar
        </Button>
      </div>
      {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
    </Card>
  )
}

function ReporteUso({ equipos, categorias }) {
  const [formato, setFormato] = useState('pdf')
  const [desde, setDesde] = useState(haceDiasISO(6))
  const [hasta, setHasta] = useState(hoyISO())
  const [equipoId, setEquipoId] = useState('')
  const [categoriaId, setCategoriaId] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  async function descargar() {
    setError('')
    if (desde > hasta) {
      setError('La fecha "desde" no puede ser posterior a "hasta"')
      return
    }
    setCargando(true)
    try {
      const params = { formato, desde, hasta }
      if (equipoId) params.equipo_id = equipoId
      if (categoriaId) params.categoria_id = categoriaId
      await reportesApi.descargarReporteUso(params)
    } catch (err) {
      setError((await reportesApi.extraerErrorDeBlob(err)) || 'No se pudo generar el reporte')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Card>
      <CardHeader
        title="Actividades y uso"
        description="Tiempo de uso de aplicaciones por equipo, con filtros de fecha, equipo y categoría."
        actions={<FileSpreadsheet size={18} className="text-ink-400 dark:text-obsidian-muted" />}
      />
      <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <div>
          <Label>Desde</Label>
          <Input type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
        </div>
        <div>
          <Label>Hasta</Label>
          <Input type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        </div>
        <div>
          <Label>Equipo</Label>
          <Select aria-label="Equipo" value={equipoId} onChange={(e) => setEquipoId(e.target.value)}>
            <option value="">Todos los equipos</option>
            {equipos.map((eq) => (
              <option key={eq.id} value={eq.id}>
                {eq.nombre}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label>Categoría</Label>
          <Select aria-label="Categoría" value={categoriaId} onChange={(e) => setCategoriaId(e.target.value)}>
            <option value="">Todas las categorías</option>
            {categorias.map((c) => (
              <option key={c.id} value={c.id}>
                {c.nombre}
              </option>
            ))}
          </Select>
        </div>
        <SelectorFormato value={formato} onChange={setFormato} etiqueta="Formato del reporte de uso" />
      </div>
      <div className="mt-4">
        <Button leftIcon={<Download size={15} />} loading={cargando} onClick={descargar}>
          Descargar
        </Button>
      </div>
      {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
    </Card>
  )
}

function ReporteAuditoria() {
  const [formato, setFormato] = useState('pdf')
  const [desde, setDesde] = useState(haceDiasISO(29))
  const [hasta, setHasta] = useState(hoyISO())
  const [usuario, setUsuario] = useState('')
  const [entidad, setEntidad] = useState('')
  const [origen, setOrigen] = useState('')
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState('')

  async function descargar() {
    setError('')
    if (desde > hasta) {
      setError('La fecha "desde" no puede ser posterior a "hasta"')
      return
    }
    setCargando(true)
    try {
      const params = { formato, desde, hasta }
      if (usuario) params.user = usuario
      if (entidad) params.entidad = entidad
      if (origen) params.origen = origen
      await reportesApi.descargarReporteAuditoria(params)
    } catch (err) {
      setError((await reportesApi.extraerErrorDeBlob(err)) || 'No se pudo generar el reporte')
    } finally {
      setCargando(false)
    }
  }

  return (
    <Card>
      <CardHeader
        title="Auditoría"
        description="Historial de acciones de administradores y del sistema, con filtros de usuario, entidad y origen."
        actions={<ShieldCheck size={18} className="text-ink-400 dark:text-obsidian-muted" />}
      />
      <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
        <div>
          <Label>Desde</Label>
          <Input type="date" value={desde} onChange={(e) => setDesde(e.target.value)} />
        </div>
        <div>
          <Label>Hasta</Label>
          <Input type="date" value={hasta} onChange={(e) => setHasta(e.target.value)} />
        </div>
        <div>
          <Label>Usuario</Label>
          <Input value={usuario} onChange={(e) => setUsuario(e.target.value)} placeholder="usuario" />
        </div>
        <div>
          <Label>Entidad</Label>
          <Input value={entidad} onChange={(e) => setEntidad(e.target.value)} placeholder="equipo, usuario..." />
        </div>
        <div>
          <Label>Origen</Label>
          <Select aria-label="Origen" value={origen} onChange={(e) => setOrigen(e.target.value)}>
            {ORIGENES.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </Select>
        </div>
        <SelectorFormato value={formato} onChange={setFormato} etiqueta="Formato del reporte de auditoría" />
      </div>
      <div className="mt-4">
        <Button leftIcon={<Download size={15} />} loading={cargando} onClick={descargar}>
          Descargar
        </Button>
      </div>
      {error && <p className="mt-3 text-sm text-red-600 dark:text-red-400">{error}</p>}
    </Card>
  )
}

export default function Reportes() {
  const [equipos, setEquipos] = useState([])
  const [categorias, setCategorias] = useState([])

  useEffect(() => {
    equiposApi.listarEquipos().then(setEquipos).catch(() => {})
    categoriasApi.listarCategorias().then(setCategorias).catch(() => {})
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900 dark:text-white">Reportes</h1>
        <p className="mt-1 text-sm text-ink-500 dark:text-obsidian-muted">
          Genera reportes en PDF, CSV o Excel con el membrete de Nexus Obsidian.
        </p>
      </div>

      <ReporteGeneral />
      <ReporteUso equipos={equipos} categorias={categorias} />
      <ReporteAuditoria />
    </div>
  )
}
