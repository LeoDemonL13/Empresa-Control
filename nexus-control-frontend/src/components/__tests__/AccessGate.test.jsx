import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { RequiereSesion, RequiereRol } from '../AccessGate'
import { AuthProvider } from '../../context/AuthContext'

vi.mock('../../api/auth', () => ({
  login: vi.fn(),
  verify2fa: vi.fn(),
  refresh: vi.fn(),
  logout: vi.fn(),
}))

import * as authApi from '../../api/auth'

function montar(initialPath) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<div>pantalla de login</div>} />
          <Route element={<RequiereSesion />}>
            <Route path="/" element={<div>inicio protegido</div>} />
            <Route element={<RequiereRol roles={['super_admin']} />}>
              <Route path="/administradores" element={<div>solo super admin</div>} />
            </Route>
          </Route>
        </Routes>
      </AuthProvider>
    </MemoryRouter>,
  )
}

it('redirige a login cuando no hay sesión', async () => {
  authApi.refresh.mockRejectedValue({ response: { status: 401 } })
  montar('/')
  await waitFor(() => expect(screen.getByText('pantalla de login')).toBeInTheDocument())
})

it('permite el paso cuando la sesión se restaura', async () => {
  authApi.refresh.mockResolvedValue({ token: 'abc', user: { id: 1, username: 'ana', role: 'admin' } })
  montar('/')
  await waitFor(() => expect(screen.getByText('inicio protegido')).toBeInTheDocument())
})

it('bloquea /administradores a un administrador que no es super admin', async () => {
  authApi.refresh.mockResolvedValue({ token: 'abc', user: { id: 1, username: 'ana', role: 'admin' } })
  montar('/administradores')
  await waitFor(() => expect(screen.getByText('inicio protegido')).toBeInTheDocument())
})

it('permite /administradores a un super admin', async () => {
  authApi.refresh.mockResolvedValue({ token: 'abc', user: { id: 1, username: 'root', role: 'super_admin' } })
  montar('/administradores')
  await waitFor(() => expect(screen.getByText('solo super admin')).toBeInTheDocument())
})
