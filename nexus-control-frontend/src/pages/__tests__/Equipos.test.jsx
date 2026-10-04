import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import Equipos from '../Equipos'
import { AuthProvider } from '../../context/AuthContext'
import { SocketProvider } from '../../context/SocketContext'

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  verify2fa: vi.fn(),
  refresh: vi.fn().mockResolvedValue({
    token: 'abc',
    user: { id: 1, username: 'root', role: 'super_admin' },
  }),
  logout: vi.fn(),
}))

vi.mock('../../api/equipos', () => ({
  listarEquipos: vi.fn(),
  obtenerEquipo: vi.fn(),
  crearEquipo: vi.fn(),
  actualizarEquipo: vi.fn(),
  eliminarEquipo: vi.fn(),
  regenerarEnrolamiento: vi.fn(),
  listarAplicaciones: vi.fn(),
  agregarAplicacion: vi.fn(),
  actualizarPolitica: vi.fn(),
  quitarAplicacion: vi.fn(),
  obtenerUso: vi.fn(),
}))

vi.mock('../../api/categorias', () => ({
  listarCategorias: vi.fn(),
}))

vi.mock('socket.io-client', () => ({
  io: () => ({ on: vi.fn(), off: vi.fn(), disconnect: vi.fn() }),
}))

import * as equiposApi from '../../api/equipos'
import * as categoriasApi from '../../api/categorias'

function montar() {
  return render(
    <AuthProvider>
      <SocketProvider>
        <Equipos />
      </SocketProvider>
    </AuthProvider>,
  )
}

beforeEach(() => {
  categoriasApi.listarCategorias.mockResolvedValue([{ id: 1, nombre: 'Ventas', total_equipos: 1 }])
  equiposApi.listarEquipos.mockResolvedValue([
    {
      id: 1,
      nombre: 'PC-Recepcion',
      usuario_asignado: 'Ana',
      ip: '192.168.1.10',
      mac: 'AA:BB:CC:DD:EE:FF',
      hostname: 'PC-RECEP',
      categoria: { id: 1, nombre: 'Ventas' },
      en_linea: true,
      enrolado: false,
      agente_version: null,
    },
  ])
})

it('lista los equipos existentes con su estado', async () => {
  montar()
  await waitFor(() => expect(screen.getByText('PC-Recepcion')).toBeInTheDocument())
  expect(screen.getAllByText('En línea').length).toBeGreaterThan(0)
  expect(screen.getByText('Ventas')).toBeInTheDocument()
})

it('muestra el mensaje de sin resultados cuando el filtro no encuentra nada', async () => {
  equiposApi.listarEquipos.mockResolvedValueOnce([])
  montar()
  await waitFor(() => expect(screen.getByText('No hay equipos con estos filtros.')).toBeInTheDocument())
})

it('crea un equipo nuevo y muestra el código de enrolamiento', async () => {
  equiposApi.crearEquipo.mockResolvedValue({
    id: 2,
    nombre: 'PC-Nuevo',
    codigo_enrolamiento: 'ABCDE-FGHIJ',
    codigo_expira_at: new Date().toISOString(),
  })
  montar()
  await waitFor(() => expect(screen.getByText('PC-Recepcion')).toBeInTheDocument())

  await userEvent.click(screen.getByRole('button', { name: 'Agregar equipo' }))
  await userEvent.type(screen.getByPlaceholderText('PC-Recepcion'), 'PC-Nuevo')
  await userEvent.click(screen.getByRole('button', { name: 'Crear equipo' }))

  await waitFor(() => expect(screen.getByText('ABCDE-FGHIJ')).toBeInTheDocument())
  expect(equiposApi.crearEquipo).toHaveBeenCalledWith(
    expect.objectContaining({ nombre: 'PC-Nuevo' }),
  )
})

it('abre el detalle de un equipo al hacer click en Ver', async () => {
  equiposApi.obtenerEquipo.mockResolvedValue({
    id: 1,
    nombre: 'PC-Recepcion',
    usuario_asignado: 'Ana',
    ip: '192.168.1.10',
    mac: 'AA:BB:CC:DD:EE:FF',
    hostname: 'PC-RECEP',
    sistema_operativo: 'Windows 11',
    categoria: { id: 1, nombre: 'Ventas' },
    en_linea: true,
    enrolado: false,
    agente_version: null,
    codigo_pendiente: null,
  })
  montar()
  await waitFor(() => expect(screen.getByText('PC-Recepcion')).toBeInTheDocument())
  await userEvent.click(screen.getByRole('button', { name: 'Ver' }))
  await waitFor(() => expect(screen.getByText('Sin código de enrolamiento activo')).toBeInTheDocument())
  expect(screen.getByText('Windows 11')).toBeInTheDocument()
})

it('muestra la matriz de control en la pestaña de aplicaciones', async () => {
  equiposApi.obtenerEquipo.mockResolvedValue({
    id: 1,
    nombre: 'PC-Recepcion',
    usuario_asignado: 'Ana',
    ip: '192.168.1.10',
    mac: 'AA:BB:CC:DD:EE:FF',
    hostname: 'PC-RECEP',
    sistema_operativo: 'Windows 11',
    categoria: { id: 1, nombre: 'Ventas' },
    en_linea: true,
    enrolado: false,
    agente_version: null,
    codigo_pendiente: null,
  })
  equiposApi.listarAplicaciones.mockResolvedValue([
    {
      id: 5,
      aplicacion: { id: 5, nombre: 'Discord', ejecutable: 'discord.exe' },
      instalada: true,
      estado: 'bloqueada',
      tipo_uso: 'sin_limite',
      limite_minutos: null,
      uso_hoy_segundos: 0,
      uso_7dias_segundos: 0,
    },
  ])

  montar()
  await waitFor(() => expect(screen.getByText('PC-Recepcion')).toBeInTheDocument())
  await userEvent.click(screen.getByRole('button', { name: 'Ver' }))
  await waitFor(() => expect(screen.getByText('Sin código de enrolamiento activo')).toBeInTheDocument())

  await userEvent.click(screen.getByRole('button', { name: 'Aplicaciones' }))
  await waitFor(() => expect(screen.getByText('Discord')).toBeInTheDocument())
  expect(screen.getAllByText('Bloqueada').length).toBeGreaterThan(0)
})

it('bloquea una aplicación desde la matriz de control', async () => {
  equiposApi.obtenerEquipo.mockResolvedValue({
    id: 1,
    nombre: 'PC-Recepcion',
    usuario_asignado: 'Ana',
    categoria: { id: 1, nombre: 'Ventas' },
    en_linea: true,
    enrolado: false,
    agente_version: null,
    codigo_pendiente: null,
  })
  equiposApi.listarAplicaciones.mockResolvedValue([
    {
      id: 5,
      aplicacion: { id: 5, nombre: 'Discord', ejecutable: 'discord.exe' },
      instalada: true,
      estado: 'permitida',
      tipo_uso: 'sin_limite',
      limite_minutos: null,
      uso_hoy_segundos: 0,
      uso_7dias_segundos: 0,
    },
  ])
  equiposApi.actualizarPolitica.mockResolvedValue({})

  montar()
  await waitFor(() => expect(screen.getByText('PC-Recepcion')).toBeInTheDocument())
  await userEvent.click(screen.getByRole('button', { name: 'Ver' }))
  await userEvent.click(screen.getByRole('button', { name: 'Aplicaciones' }))
  await waitFor(() => expect(screen.getByText('Discord')).toBeInTheDocument())

  await userEvent.click(screen.getByRole('button', { name: 'Bloqueada' }))
  await waitFor(() => expect(equiposApi.actualizarPolitica).toHaveBeenCalledWith(1, 5, { estado: 'bloqueada' }))
})

it('agrega una nueva aplicación a la matriz de control', async () => {
  equiposApi.obtenerEquipo.mockResolvedValue({
    id: 1,
    nombre: 'PC-Recepcion',
    usuario_asignado: 'Ana',
    categoria: { id: 1, nombre: 'Ventas' },
    en_linea: true,
    enrolado: false,
    agente_version: null,
    codigo_pendiente: null,
  })
  equiposApi.listarAplicaciones.mockResolvedValue([])
  equiposApi.agregarAplicacion.mockResolvedValue({
    id: 9,
    aplicacion: { id: 9, nombre: 'discord.exe', ejecutable: 'discord.exe' },
    estado: 'permitida',
    tipo_uso: 'sin_limite',
    uso_hoy_segundos: 0,
    uso_7dias_segundos: 0,
  })

  montar()
  await waitFor(() => expect(screen.getByText('PC-Recepcion')).toBeInTheDocument())
  await userEvent.click(screen.getByRole('button', { name: 'Ver' }))
  await userEvent.click(screen.getByRole('button', { name: 'Aplicaciones' }))
  await waitFor(() => expect(screen.getByText(/no tiene aplicaciones/)).toBeInTheDocument())

  await userEvent.type(screen.getByPlaceholderText('discord.exe'), 'discord.exe')
  await userEvent.click(screen.getByRole('button', { name: 'Agregar' }))

  await waitFor(() => expect(equiposApi.agregarAplicacion).toHaveBeenCalledWith(1, { ejecutable: 'discord.exe' }))
})
