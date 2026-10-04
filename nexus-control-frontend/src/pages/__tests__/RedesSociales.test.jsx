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

vi.mock('../../api/redesSociales', () => ({
  listarConexiones: vi.fn(),
  obtenerUrlConexion: vi.fn(),
  actualizarSeguimientoCuenta: vi.fn(),
  sincronizarConexion: vi.fn(),
  sincronizarTodas: vi.fn(),
  desconectarConexion: vi.fn(),
  obtenerSalud: vi.fn(),
  obtenerEstadoSistema: vi.fn(),
  obtenerResumen: vi.fn(),
}))

vi.mock('socket.io-client', () => ({
  io: () => ({ on: vi.fn(), off: vi.fn(), disconnect: vi.fn() }),
}))

import * as authApi from '../../api/auth'
import * as redesApi from '../../api/redesSociales'

const PLATAFORMAS_ORDEN = ['facebook', 'instagram', 'tiktok', 'youtube']

function conexionVacia(plataforma) {
  return {
    plataforma,
    conectada: false,
    estado: 'DISCONNECTED',
    icono: '⚫',
    estado_texto: 'No conectado',
    configurada: true,
    cuenta_externa: null,
    cuentas: [],
    ultima_sincronizacion: null,
    proxima_sincronizacion: null,
    ultimo_error: null,
    errores_consecutivos: 0,
    conectado_por: null,
    conectado_at: null,
  }
}

function conexionesVacias() {
  return PLATAFORMAS_ORDEN.map(conexionVacia)
}

function montar(initialEntries = ['/redes-sociales']) {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
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
  redesApi.listarConexiones.mockResolvedValue(conexionesVacias())
  redesApi.obtenerEstadoSistema.mockResolvedValue({
    intervalo_minutos: 15,
    plataformas: PLATAFORMAS_ORDEN.map((plataforma) => ({
      plataforma, conectada: false, estado: 'DISCONNECTED', ultima_sincronizacion: null,
      proxima_sincronizacion: null, ultimo_tiempo_respuesta_ms: null, ultimos_elementos_actualizados: null,
      ultimo_resultado: null,
    })),
  })
  redesApi.obtenerResumen.mockResolvedValue({
    desde: '2026-01-01T00:00:00Z', hasta: '2026-01-08T00:00:00Z', plataforma: null,
    publicaciones: 0, interacciones: 0, impresiones: null, tasa_engagement_promedio: null,
    seguidores_inicio: null, seguidores_fin: null, mejor_publicacion: null, peor_publicacion: null,
    por_cuenta: [], narrativa: 'En los últimos 7.0 día(s), Todas las redes registró 0 publicación(es).',
  })
})

it('muestra las 4 plataformas soportadas', async () => {
  comoSuperAdmin()
  montar()
  await waitFor(() => expect(screen.getByText('Facebook')).toBeInTheDocument())
  expect(screen.getByText('Instagram')).toBeInTheDocument()
  expect(screen.getByText('TikTok')).toBeInTheDocument()
  expect(screen.getByText('YouTube')).toBeInTheDocument()
  expect(screen.getAllByText(/No conectado/)).toHaveLength(4)
})

it('un administrador normal no ve el botón para conectar plataformas', async () => {
  comoAdmin()
  montar()
  await waitFor(() => expect(screen.getByText('Facebook')).toBeInTheDocument())
  expect(screen.queryByText(/Conectar con/)).not.toBeInTheDocument()
  expect(
    screen.getByText(/Solo el súper administrador puede conectar, reconectar o desconectar/),
  ).toBeInTheDocument()
})

it('el súper administrador inicia la conexión con Facebook', async () => {
  comoSuperAdmin()
  redesApi.obtenerUrlConexion.mockResolvedValue({ url: 'https://www.facebook.com/oauth?state=x' })
  montar()
  await waitFor(() => expect(screen.getByText('Facebook')).toBeInTheDocument())

  await userEvent.click(screen.getByRole('button', { name: /Conectar con Facebook/i }))

  await waitFor(() => expect(redesApi.obtenerUrlConexion).toHaveBeenCalledWith('facebook'))
})

it('muestra un aviso cuando la plataforma no está configurada en el servidor', async () => {
  comoSuperAdmin()
  redesApi.listarConexiones.mockResolvedValue([
    { ...conexionVacia('facebook'), configurada: false },
    ...conexionesVacias().slice(1),
  ])
  montar()
  await waitFor(() =>
    expect(screen.getByText(/no tiene configuradas sus credenciales de aplicación/)).toBeInTheDocument(),
  )
  expect(screen.queryByRole('button', { name: /Conectar con Facebook/i })).not.toBeInTheDocument()
})

it('sincroniza una plataforma conectada y avisa del resultado', async () => {
  comoSuperAdmin()
  redesApi.listarConexiones.mockResolvedValue([
    {
      ...conexionVacia('facebook'), conectada: true, estado: 'CONNECTED', icono: '🟢', estado_texto: 'Conectado',
      cuenta_externa: 'Empresa Demo',
    },
    ...conexionesVacias().slice(1),
  ])
  redesApi.sincronizarConexion.mockResolvedValue({ ok: true, error: null, conexion: {} })
  montar()
  await waitFor(() => expect(screen.getByRole('button', { name: /Sincronizar ahora/i })).toBeInTheDocument())

  await userEvent.click(screen.getByRole('button', { name: /Sincronizar ahora/i }))

  await waitFor(() => expect(redesApi.sincronizarConexion).toHaveBeenCalledWith('facebook'))
})

it('abre el panel de administración y permite alternar el seguimiento de una cuenta', async () => {
  comoSuperAdmin()
  redesApi.listarConexiones.mockResolvedValue([
    {
      ...conexionVacia('facebook'), conectada: true, estado: 'CONNECTED', icono: '🟢', estado_texto: 'Conectado',
      cuenta_externa: 'Empresa Demo',
    },
    ...conexionesVacias().slice(1),
  ])
  redesApi.obtenerSalud.mockResolvedValue({
    plataforma: 'facebook', conectada: true, estado: 'CONNECTED', icono: '🟢', estado_texto: 'Conectado',
    configurada: true, cuenta_externa: 'Empresa Demo', alcance: 'pages_show_list',
    cuentas: [{ id: 10, id_externo: 'pagina-1', nombre: 'Página de prueba', usuario: null, url_imagen: null, seguimiento_activo: true }],
    ultima_sincronizacion: null, proxima_sincronizacion: null, ultimo_error: null, errores_consecutivos: 0,
    conectado_por: 'root@nexus.mx', conectado_at: null, errores_recientes: [],
  })
  redesApi.actualizarSeguimientoCuenta.mockResolvedValue({ ok: true })
  montar()
  await waitFor(() => expect(screen.getByRole('button', { name: 'Administrar' })).toBeInTheDocument())

  await userEvent.click(screen.getByRole('button', { name: 'Administrar' }))

  await waitFor(() => expect(screen.getByText('Página de prueba')).toBeInTheDocument())
  await userEvent.click(screen.getByRole('button', { name: 'Siguiendo' }))

  await waitFor(() =>
    expect(redesApi.actualizarSeguimientoCuenta).toHaveBeenCalledWith('facebook', 10, false),
  )
})

it('un administrador normal ve el panel de administración en solo lectura', async () => {
  comoAdmin()
  redesApi.listarConexiones.mockResolvedValue([
    {
      ...conexionVacia('facebook'), conectada: true, estado: 'CONNECTED', icono: '🟢', estado_texto: 'Conectado',
      cuenta_externa: 'Empresa Demo',
    },
    ...conexionesVacias().slice(1),
  ])
  redesApi.obtenerSalud.mockResolvedValue({
    plataforma: 'facebook', conectada: true, estado: 'CONNECTED', icono: '🟢', estado_texto: 'Conectado',
    configurada: true, cuenta_externa: 'Empresa Demo', alcance: 'pages_show_list',
    cuentas: [], ultima_sincronizacion: null, proxima_sincronizacion: null, ultimo_error: null,
    errores_consecutivos: 0, conectado_por: 'root@nexus.mx', conectado_at: null, errores_recientes: [],
  })
  montar()
  await waitFor(() => expect(screen.getByRole('button', { name: 'Administrar' })).toBeInTheDocument())
  await userEvent.click(screen.getByRole('button', { name: 'Administrar' }))

  await waitFor(() => expect(screen.getByText('Conectado')).toBeInTheDocument())
  expect(screen.queryByRole('button', { name: 'Reconectar' })).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Desconectar' })).not.toBeInTheDocument()
})

it('muestra el resumen de actividad con la narrativa generada', async () => {
  comoAdmin()
  montar()
  await waitFor(() =>
    expect(screen.getByText(/En los últimos 7.0 día\(s\)/)).toBeInTheDocument(),
  )
})

it('muestra el estado del sistema con el intervalo configurado', async () => {
  comoAdmin()
  montar()
  await waitFor(() => expect(screen.getByText(/cada 15 min/)).toBeInTheDocument())
})

it('avisa cuando la plataforma quedó conectada tras volver del proveedor', async () => {
  comoSuperAdmin()
  montar(['/redes-sociales?conectado=facebook'])
  await waitFor(() => expect(screen.getByText('Facebook')).toBeInTheDocument())
})
