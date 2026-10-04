import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { vi } from 'vitest'
import RedesSociales from '../RedesSociales'
import { AuthProvider } from '../../context/AuthContext'
import { SocketProvider } from '../../context/SocketContext'

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  verify2fa: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
}))

vi.mock('../../api/conexionesSociales', () => ({
  listarConexiones: vi.fn(),
  guardarConexion: vi.fn(),
  eliminarConexion: vi.fn(),
  sincronizarConexion: vi.fn(),
  sincronizarTodas: vi.fn(),
}))

vi.mock('socket.io-client', () => ({
  io: () => ({ on: vi.fn(), off: vi.fn(), disconnect: vi.fn() }),
}))

import * as authApi from '../../api/auth'
import * as conexionesApi from '../../api/conexionesSociales'

const PLATAFORMAS_ORDEN = ['facebook', 'instagram', 'tiktok', 'youtube', 'x']

function conexionesVacias() {
  return PLATAFORMAS_ORDEN.map((plataforma) => ({
    plataforma,
    conectada: false,
    ultima_sincronizacion: null,
    ultimo_error: null,
    actualizado_por: null,
    updated_at: null,
  }))
}

function montar() {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <SocketProvider>
          <RedesSociales />
        </SocketProvider>
      </AuthProvider>
    </MemoryRouter>,
  )
}

function comoSuperAdmin() {
  authApi.refresh.mockResolvedValue({
    token: 'abc',
    user: { id: 1, username: 'root@nexus.mx', role: 'super_admin', full_name: 'Root' },
  })
}

function comoAdmin() {
  authApi.refresh.mockResolvedValue({
    token: 'abc',
    user: { id: 2, username: 'ana@nexus.mx', role: 'admin', full_name: 'Ana' },
  })
}

beforeEach(() => {
  conexionesApi.listarConexiones.mockResolvedValue(conexionesVacias())
})

it('muestra las 5 plataformas soportadas', async () => {
  comoSuperAdmin()
  montar()
  await waitFor(() => expect(screen.getByText('Facebook')).toBeInTheDocument())
  expect(screen.getByText('Instagram')).toBeInTheDocument()
  expect(screen.getByText('TikTok')).toBeInTheDocument()
  expect(screen.getByText('YouTube')).toBeInTheDocument()
  expect(screen.getByText('X', { selector: 'p' })).toBeInTheDocument()
  expect(screen.getAllByText('No conectada')).toHaveLength(5)
})

it('un administrador normal no ve los botones para guardar o quitar credenciales', async () => {
  comoAdmin()
  montar()
  await waitFor(() => expect(screen.getByText('Facebook')).toBeInTheDocument())
  expect(screen.queryByText('Configurar')).not.toBeInTheDocument()
  expect(
    screen.getByText(
      'Solo el súper administrador puede guardar o quitar credenciales; cualquier administrador puede sincronizar.',
    ),
  ).toBeInTheDocument()
})

it('el súper administrador guarda las credenciales de YouTube', async () => {
  comoSuperAdmin()
  conexionesApi.guardarConexion.mockResolvedValue({
    plataforma: 'youtube', conectada: true, ultima_sincronizacion: null, ultimo_error: null,
  })
  montar()
  await waitFor(() => expect(screen.getByText('YouTube')).toBeInTheDocument())

  const botones = screen.getAllByRole('button', { name: 'Configurar' })
  await userEvent.click(botones[PLATAFORMAS_ORDEN.indexOf('youtube')])

  await userEvent.type(screen.getByPlaceholderText('AIzaSy...'), 'clave-de-prueba')
  await userEvent.type(screen.getByPlaceholderText('UCxxxxxxxxxxxxxxxxxxxxxx'), 'UC12345')
  await userEvent.click(screen.getByRole('button', { name: 'Guardar credenciales' }))

  await waitFor(() =>
    expect(conexionesApi.guardarConexion).toHaveBeenCalledWith('youtube', {
      clave_api: 'clave-de-prueba',
      id_canal: 'UC12345',
    }),
  )
})

it('nunca expone las credenciales ya guardadas en la tarjeta', async () => {
  comoSuperAdmin()
  conexionesApi.listarConexiones.mockResolvedValue([
    {
      plataforma: 'facebook',
      conectada: true,
      ultima_sincronizacion: '2026-10-01T10:00:00Z',
      ultimo_error: null,
      actualizado_por: 'root@nexus.mx',
      updated_at: '2026-10-01T10:00:00Z',
    },
    ...conexionesVacias().slice(1),
  ])
  montar()
  await waitFor(() => expect(screen.getByText('Conectada')).toBeInTheDocument())
  expect(screen.queryByText(/EAA|token/i)).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: /Sincronizar ahora/i })).toBeInTheDocument()
})

it('sincroniza una plataforma conectada y avisa del resultado', async () => {
  comoSuperAdmin()
  conexionesApi.listarConexiones.mockResolvedValue([
    { plataforma: 'facebook', conectada: true, ultima_sincronizacion: null, ultimo_error: null, actualizado_por: null, updated_at: null },
    ...conexionesVacias().slice(1),
  ])
  conexionesApi.sincronizarConexion.mockResolvedValue({ ok: true, error: null, conexion: {} })
  montar()
  await waitFor(() => expect(screen.getByRole('button', { name: /Sincronizar ahora/i })).toBeInTheDocument())

  await userEvent.click(screen.getByRole('button', { name: /Sincronizar ahora/i }))

  await waitFor(() => expect(conexionesApi.sincronizarConexion).toHaveBeenCalledWith('facebook'))
})

it('el súper administrador puede desconectar una plataforma', async () => {
  comoSuperAdmin()
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  conexionesApi.listarConexiones.mockResolvedValue([
    { plataforma: 'facebook', conectada: true, ultima_sincronizacion: null, ultimo_error: null, actualizado_por: null, updated_at: null },
    ...conexionesVacias().slice(1),
  ])
  conexionesApi.eliminarConexion.mockResolvedValue({ ok: true })
  montar()
  await waitFor(() => expect(screen.getByRole('button', { name: /Desconectar/i })).toBeInTheDocument())

  await userEvent.click(screen.getByRole('button', { name: /Desconectar/i }))

  await waitFor(() => expect(conexionesApi.eliminarConexion).toHaveBeenCalledWith('facebook'))
})
