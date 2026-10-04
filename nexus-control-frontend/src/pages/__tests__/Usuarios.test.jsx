import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import Usuarios from '../Usuarios'
import { AuthProvider } from '../../context/AuthContext'

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  verify2fa: vi.fn(),
  refresh: vi.fn().mockResolvedValue({
    token: 'abc',
    user: { id: 1, username: 'root', role: 'super_admin' },
  }),
  logout: vi.fn(),
}))

vi.mock('../../api/users', () => ({
  listarAdministradores: vi.fn(),
  crearAdministrador: vi.fn(),
  actualizarAdministrador: vi.fn(),
  desactivarAdministrador: vi.fn(),
  reactivarAdministrador: vi.fn(),
  resetearPassword: vi.fn(),
  revocarSesionesDe: vi.fn(),
}))

import * as usersApi from '../../api/users'

function montar() {
  return render(
    <AuthProvider>
      <Usuarios />
    </AuthProvider>,
  )
}

beforeEach(() => {
  usersApi.listarAdministradores.mockResolvedValue([
    { id: 1, username: 'root', role: 'super_admin', activo: true, totp_enabled: true, full_name: 'Root' },
    { id: 2, username: 'ana', role: 'admin', activo: true, totp_enabled: false, full_name: 'Ana' },
  ])
})

it('lista los administradores existentes', async () => {
  montar()
  await waitFor(() => expect(screen.getByText('ana')).toBeInTheDocument())
  expect(screen.getByText('root')).toBeInTheDocument()
  expect(screen.getAllByText('Súper admin').length).toBeGreaterThan(0)
})

it('crea un nuevo administrador', async () => {
  usersApi.crearAdministrador.mockResolvedValue({ id: 3, username: 'nuevo', role: 'admin' })
  montar()
  await waitFor(() => expect(screen.getByText('ana')).toBeInTheDocument())
  await userEvent.click(screen.getByRole('button', { name: 'Agregar' }))
  await userEvent.type(screen.getByPlaceholderText('usuario@nexus.mx'), 'nuevo@nexus.mx')
  await userEvent.type(screen.getByPlaceholderText('Mínimo 12 caracteres'), 'Cl4ve-Valida-2026!')
  await userEvent.click(screen.getByRole('button', { name: 'Crear administrador' }))
  await waitFor(() => expect(usersApi.crearAdministrador).toHaveBeenCalledWith({
    username: 'nuevo@nexus.mx',
    password: 'Cl4ve-Valida-2026!',
    full_name: '',
  }))
})
