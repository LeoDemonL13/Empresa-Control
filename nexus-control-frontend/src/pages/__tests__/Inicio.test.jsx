import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import Inicio from '../Inicio'
import { AuthProvider } from '../../context/AuthContext'
import { SocketProvider } from '../../context/SocketContext'

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  verify2fa: vi.fn(),
  refresh: vi.fn().mockResolvedValue({
    token: 'abc',
    user: { id: 1, username: 'root', role: 'super_admin', full_name: 'Root' },
  }),
  logout: vi.fn(),
  actividadReciente: vi.fn(),
}))

vi.mock('../../api/dashboard', () => ({
  obtenerResumen: vi.fn(),
}))

vi.mock('../../api/metricas', () => ({
  listarMetricas: vi.fn(),
  guardarMetrica: vi.fn(),
  eliminarMetrica: vi.fn(),
}))

vi.mock('socket.io-client', () => ({
  io: () => ({ on: vi.fn(), off: vi.fn(), disconnect: vi.fn() }),
}))

import * as authApi from '../../api/auth'
import * as dashboardApi from '../../api/dashboard'
import * as metricasApi from '../../api/metricas'

function montar() {
  return render(
    <AuthProvider>
      <SocketProvider>
        <Inicio />
      </SocketProvider>
    </AuthProvider>,
  )
}

beforeEach(() => {
  authApi.actividadReciente.mockResolvedValue([])
  dashboardApi.obtenerResumen.mockResolvedValue({
    equipos_registrados: 12,
    en_linea: 9,
    fuera_linea: 3,
    apps_bloqueadas: 4,
    top_aplicaciones: [{ nombre: 'Discord', ejecutable: 'discord.exe', segundos: 7260 }],
  })
  metricasApi.listarMetricas.mockResolvedValue([])
})

it('muestra los indicadores del panel', async () => {
  montar()
  await waitFor(() => expect(screen.getByText('12')).toBeInTheDocument())
  expect(screen.getByText('9')).toBeInTheDocument()
  expect(screen.getByText('3')).toBeInTheDocument()
  expect(screen.getByText('4')).toBeInTheDocument()
})

it('muestra la aplicación más usada', async () => {
  montar()
  await waitFor(() => expect(screen.getByText('Discord')).toBeInTheDocument())
  expect(screen.getByText('2 h 1 min')).toBeInTheDocument()
})

it('muestra el estado vacío de redes sociales cuando no hay métricas', async () => {
  montar()
  await waitFor(() =>
    expect(
      screen.getByText('Todavía no hay métricas de redes sociales. Agrega una para empezar a llevar el control.'),
    ).toBeInTheDocument(),
  )
})

it('agrega una nueva métrica de red social', async () => {
  metricasApi.guardarMetrica.mockResolvedValue({})
  montar()
  await waitFor(() => expect(screen.getByText('12')).toBeInTheDocument())

  await userEvent.click(screen.getByRole('button', { name: 'Agregar' }))
  await userEvent.type(screen.getByPlaceholderText('Instagram, Facebook, TikTok...'), 'Instagram')
  await userEvent.click(screen.getByRole('button', { name: 'Guardar' }))

  await waitFor(() =>
    expect(metricasApi.guardarMetrica).toHaveBeenCalledWith({
      red_social: 'Instagram',
      me_gusta: 0,
      interacciones: 0,
      impresiones: 0,
      engagement: 0,
    }),
  )
})

it('lista las métricas existentes', async () => {
  metricasApi.listarMetricas.mockResolvedValue([
    { id: 1, red_social: 'instagram', me_gusta: 120, interacciones: 45, impresiones: 900, engagement: 5.5 },
  ])
  montar()
  await waitFor(() => expect(screen.getByText('instagram')).toBeInTheDocument())
  expect(screen.getByText('120')).toBeInTheDocument()
  expect(screen.getByText('5.5%')).toBeInTheDocument()
})
