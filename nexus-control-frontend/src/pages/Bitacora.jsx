import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { Badge, Button, Card } from '../components/ui'
import Input, { Label } from '../components/ui/Input'
import Modal from '../components/ui/Modal'
import * as bitacoraApi from '../api/bitacora'

const ORIGEN_TONO = { panel: 'brand', agente: 'info', sistema: 'neutral' }

export default function Bitacora() {
  const [items, setItems] = useState([])
  const [meta, setMeta] = useState({ page: 1, pages: 1, total: 0, has_next: false, has_prev: false })
  const [filtros, setFiltros] = useState({ user: '', entidad: '', fecha: '' })
  const [cargando, setCargando] = useState(true)
  const [detalle, setDetalle] = useState(null)

  function cargar(page = 1) {
    setCargando(true)
    const params = { page, per_page: 20 }
    if (filtros.user) params.user = filtros.user
    if (filtros.entidad) params.entidad = filtros.entidad
    if (filtros.fecha) params.fecha = filtros.fecha
    bitacoraApi
      .listarBitacora(params)
      .then((data) => {
        setItems(data.items)
        setMeta(data)
      })
      .finally(() => setCargando(false))
  }

  useEffect(() => {
    cargar(1)
  }, [])

  function aplicarFiltros(e) {
    e.preventDefault()
    cargar(1)
  }

  async function verDetalle(id) {
    const data = await bitacoraApi.detalleBitacora(id)
    setDetalle(data)
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink-900 dark:text-white">Bitácora</h1>
        <p className="mt-1 text-sm text-ink-500 dark:text-obsidian-muted">Historial de cambios y acciones de los administradores.</p>
      </div>

      <Card>
        <form onSubmit={aplicarFiltros} className="grid gap-3 sm:grid-cols-4">
          <div>
            <Label>Usuario</Label>
            <Input value={filtros.user} onChange={(e) => setFiltros((f) => ({ ...f, user: e.target.value }))} placeholder="usuario" />
          </div>
          <div>
            <Label>Entidad</Label>
            <Input value={filtros.entidad} onChange={(e) => setFiltros((f) => ({ ...f, entidad: e.target.value }))} placeholder="usuario, equipo..." />
          </div>
          <div>
            <Label>Fecha</Label>
            <Input type="date" value={filtros.fecha} onChange={(e) => setFiltros((f) => ({ ...f, fecha: e.target.value }))} />
          </div>
          <div className="flex items-end">
            <Button type="submit" className="w-full">
              Filtrar
            </Button>
          </div>
        </form>
      </Card>

      <Card padded={false}>
        <div className="overflow-x-auto scrollbar-thin">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-ink-200 text-left text-xs uppercase tracking-wide text-ink-500 dark:border-obsidian-line dark:text-obsidian-muted">
                <th className="px-4 py-3">Fecha</th>
                <th className="px-4 py-3">Usuario</th>
                <th className="px-4 py-3">Acción</th>
                <th className="px-4 py-3">Entidad</th>
                <th className="px-4 py-3">Origen</th>
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
              {!cargando && items.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-ink-500 dark:text-obsidian-muted">
                    Sin registros
                  </td>
                </tr>
              )}
              {!cargando &&
                items.map((item) => (
                  <tr
                    key={item.id}
                    onClick={() => verDetalle(item.id)}
                    className="cursor-pointer border-b border-ink-100 last:border-0 hover:bg-ink-50 dark:border-obsidian-line dark:hover:bg-white/5"
                  >
                    <td className="whitespace-nowrap px-4 py-3 text-ink-500 dark:text-obsidian-muted">
                      {item.created_at ? new Date(item.created_at).toLocaleString() : '—'}
                    </td>
                    <td className="px-4 py-3 font-medium text-ink-900 dark:text-white">{item.user}</td>
                    <td className="px-4 py-3 text-ink-700 dark:text-ink-200">{item.action}</td>
                    <td className="px-4 py-3 text-ink-500 dark:text-obsidian-muted">{item.entidad || '—'}</td>
                    <td className="px-4 py-3">
                      <Badge tone={ORIGEN_TONO[item.origen] || 'neutral'} mono>
                        {item.origen}
                      </Badge>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>

        <div className="flex items-center justify-between border-t border-ink-200 px-4 py-3 text-sm text-ink-500 dark:border-obsidian-line dark:text-obsidian-muted">
          <span>
            Página {meta.page} de {meta.pages || 1} · {meta.total} registros
          </span>
          <div className="flex gap-1.5">
            <Button size="icon-sm" variant="secondary" disabled={!meta.has_prev} onClick={() => cargar(meta.page - 1)}>
              <ChevronLeft size={15} />
            </Button>
            <Button size="icon-sm" variant="secondary" disabled={!meta.has_next} onClick={() => cargar(meta.page + 1)}>
              <ChevronRight size={15} />
            </Button>
          </div>
        </div>
      </Card>

      <Modal open={Boolean(detalle)} onClose={() => setDetalle(null)} title="Detalle del registro">
        {detalle && (
          <div className="space-y-3 text-sm">
            <p>
              <span className="text-ink-500 dark:text-obsidian-muted">Usuario: </span>
              {detalle.user}
            </p>
            <p>
              <span className="text-ink-500 dark:text-obsidian-muted">Acción: </span>
              {detalle.action}
            </p>
            <p>
              <span className="text-ink-500 dark:text-obsidian-muted">IP: </span>
              {detalle.ip || '—'}
            </p>
            {detalle.detalle && (
              <pre className="overflow-x-auto rounded-md bg-ink-50 p-3 text-xs dark:bg-obsidian-cardAlt">
                {JSON.stringify(detalle.detalle, null, 2)}
              </pre>
            )}
          </div>
        )}
      </Modal>
    </div>
  )
}
