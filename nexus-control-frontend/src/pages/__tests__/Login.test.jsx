import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import Login from '../Login'
import { AuthProvider } from '../../context/AuthContext'

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  verify2fa: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
}))

import * as authApi from '../../api/auth'

function montar() {
  return render(
    <MemoryRouter initialEntries={['/login']}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/" element={<div>inicio</div>} />
          <Route path="/verificar-2fa" element={<div>pantalla 2fa</div>} />
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  authApi.refresh.mockRejectedValue({ response: { status: 401 } })
})

it('login exitoso navega al inicio', async () => {
  authApi.login.mockResolvedValue({ token: 'abc', user: { id: 1, username: 'ana', role: 'admin' } })
  montar()
  await userEvent.type(screen.getByPlaceholderText('tu.usuario'), 'ana')
  await userEvent.type(screen.getByPlaceholderText('••••••••••••'), 'Cl4ve-Segura-Prueba!')
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
  await waitFor(() => expect(screen.getByText('inicio')).toBeInTheDocument())
})

it('login con 2fa navega a la pantalla de verificación', async () => {
  authApi.login.mockResolvedValue({ requires2fa: true, stepToken: 'step-123' })
  montar()
  await userEvent.type(screen.getByPlaceholderText('tu.usuario'), 'ana')
  await userEvent.type(screen.getByPlaceholderText('••••••••••••'), 'Cl4ve-Segura-Prueba!')
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
  await waitFor(() => expect(screen.getByText('pantalla 2fa')).toBeInTheDocument())
})

it('muestra el error cuando las credenciales son incorrectas', async () => {
  authApi.login.mockRejectedValue({ response: { data: { error: 'Credenciales incorrectas' } } })
  montar()
  await userEvent.type(screen.getByPlaceholderText('tu.usuario'), 'ana')
  await userEvent.type(screen.getByPlaceholderText('••••••••••••'), 'mala')
  await userEvent.click(screen.getByRole('button', { name: 'Entrar' }))
  await waitFor(() => expect(screen.getByText('Credenciales incorrectas')).toBeInTheDocument())
})
