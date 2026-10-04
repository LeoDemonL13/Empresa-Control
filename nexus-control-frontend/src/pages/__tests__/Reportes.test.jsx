import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import Reportes from '../Reportes'

vi.mock('../../api/equipos', () => ({
  listarEquipos: vi.fn(),
}))

vi.mock('../../api/categorias', () => ({
  listarCategorias: vi.fn(),
}))

vi.mock('../../api/reportes', () => ({
  descargarReporteGeneral: vi.fn(),
  descargarReporteUso: vi.fn(),
  descargarReporteAuditoria: vi.fn(),
  extraerErrorDeBlob: vi.fn(),
}))

import * as categoriasApi from '../../api/categorias'
import * as equiposApi from '../../api/equipos'
import * as reportesApi from '../../api/reportes'

beforeEach(() => {
  vi.clearAllMocks()
  equiposApi.listarEquipos.mockResolvedValue([{ id: 7, nombre: 'PC-Ventas' }])
  categoriasApi.listarCategorias.mockResolvedValue([{ id: 3, nombre: 'Ventas' }])
  reportesApi.descargarReporteGeneral.mockResolvedValue()
  reportesApi.descargarReporteUso.mockResolvedValue()
  reportesApi.descargarReporteAuditoria.mockResolvedValue()
})

it('muestra los tres tipos de reportes disponibles', async () => {
  render(<Reportes />)
  expect(screen.getByText('Reporte general')).toBeInTheDocument()
  expect(screen.getByText('Actividades y uso')).toBeInTheDocument()
  expect(screen.getByText('Auditoría')).toBeInTheDocument()
  await waitFor(() => expect(equiposApi.listarEquipos).toHaveBeenCalled())
})

it('descarga el reporte general en el formato seleccionado', async () => {
  render(<Reportes />)
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Formato del reporte general' }), 'csv')
  const botones = screen.getAllByRole('button', { name: 'Descargar' })
  await userEvent.click(botones[0])
  await waitFor(() => expect(reportesApi.descargarReporteGeneral).toHaveBeenCalledWith('csv'))
})

it('descarga el reporte de uso con los filtros elegidos', async () => {
  render(<Reportes />)
  await waitFor(() => expect(screen.getByText('PC-Ventas')).toBeInTheDocument())

  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Equipo' }), '7')
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Categoría' }), '3')
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Formato del reporte de uso' }), 'xlsx')

  const botones = screen.getAllByRole('button', { name: 'Descargar' })
  await userEvent.click(botones[1])

  await waitFor(() =>
    expect(reportesApi.descargarReporteUso).toHaveBeenCalledWith(
      expect.objectContaining({ formato: 'xlsx', equipo_id: '7', categoria_id: '3' }),
    ),
  )
})

it('no descarga el reporte de uso cuando el rango de fechas es inválido', async () => {
  render(<Reportes />)
  const botones = screen.getAllByRole('button', { name: 'Descargar' })
  const seccionUso = botones[1].closest('.nx-surface')
  const fechas = seccionUso.querySelectorAll('input[type="date"]')
  await userEvent.clear(fechas[0])
  await userEvent.type(fechas[0], '2026-10-20')
  await userEvent.clear(fechas[1])
  await userEvent.type(fechas[1], '2026-10-01')

  await userEvent.click(botones[1])

  await waitFor(() =>
    expect(screen.getByText('La fecha "desde" no puede ser posterior a "hasta"')).toBeInTheDocument(),
  )
  expect(reportesApi.descargarReporteUso).not.toHaveBeenCalled()
})

it('descarga el reporte de auditoría con los filtros de usuario, entidad y origen', async () => {
  render(<Reportes />)
  await userEvent.type(screen.getByPlaceholderText('usuario'), 'ana')
  await userEvent.type(screen.getByPlaceholderText('equipo, usuario...'), 'equipo')
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Origen' }), 'panel')
  await userEvent.selectOptions(screen.getByRole('combobox', { name: 'Formato del reporte de auditoría' }), 'pdf')

  const botones = screen.getAllByRole('button', { name: 'Descargar' })
  await userEvent.click(botones[2])

  await waitFor(() =>
    expect(reportesApi.descargarReporteAuditoria).toHaveBeenCalledWith(
      expect.objectContaining({ formato: 'pdf', user: 'ana', entidad: 'equipo', origen: 'panel' }),
    ),
  )
})

it('muestra el error devuelto por el servidor al fallar la descarga', async () => {
  reportesApi.descargarReporteGeneral.mockRejectedValue(new Error('fallo de red'))
  reportesApi.extraerErrorDeBlob.mockResolvedValue('No tienes permisos para generar este reporte')
  render(<Reportes />)

  const botones = screen.getAllByRole('button', { name: 'Descargar' })
  await userEvent.click(botones[0])

  await waitFor(() =>
    expect(screen.getByText('No tienes permisos para generar este reporte')).toBeInTheDocument(),
  )
})
