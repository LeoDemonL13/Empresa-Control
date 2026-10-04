import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { AuthProvider, useAuth } from '../AuthContext'

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  verify2fa: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
}))

import * as authApi from '../../api/auth'

function Sonda() {
  const { user, autenticado, cargando, login, verify2fa, logout } = useAuth()
  return (
    <div>
      <span data-testid="cargando">{String(cargando)}</span>
      <span data-testid="autenticado">{String(autenticado)}</span>
      <span data-testid="usuario">{user?.username || ''}</span>
      <button onClick={() => login('ana', 'clave')}>login</button>
      <button onClick={() => verify2fa('step', '123456')}>verify</button>
      <button onClick={() => logout()}>logout</button>
    </div>
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  authApi.refresh.mockRejectedValue({ response: { status: 401 } })
})

it('al montar intenta refrescar la sesión y termina de cargar', async () => {
  render(
    <AuthProvider>
      <Sonda />
    </AuthProvider>,
  )
  await waitFor(() => expect(screen.getByTestId('cargando').textContent).toBe('false'))
  expect(screen.getByTestId('autenticado').textContent).toBe('false')
})

it('login exitoso deja al usuario autenticado', async () => {
  authApi.login.mockResolvedValue({ token: 'abc', user: { id: 1, username: 'ana', role: 'admin' } })
  render(
    <AuthProvider>
      <Sonda />
    </AuthProvider>,
  )
  await waitFor(() => expect(screen.getByTestId('cargando').textContent).toBe('false'))
  await userEvent.click(screen.getByText('login'))
  await waitFor(() => expect(screen.getByTestId('autenticado').textContent).toBe('true'))
  expect(screen.getByTestId('usuario').textContent).toBe('ana')
})

it('logout limpia la sesión', async () => {
  authApi.login.mockResolvedValue({ token: 'abc', user: { id: 1, username: 'ana', role: 'admin' } })
  authApi.logout.mockResolvedValue({ ok: true })
  render(
    <AuthProvider>
      <Sonda />
    </AuthProvider>,
  )
  await waitFor(() => expect(screen.getByTestId('cargando').textContent).toBe('false'))
  await userEvent.click(screen.getByText('login'))
  await waitFor(() => expect(screen.getByTestId('autenticado').textContent).toBe('true'))
  await userEvent.click(screen.getByText('logout'))
  await waitFor(() => expect(screen.getByTestId('autenticado').textContent).toBe('false'))
})
