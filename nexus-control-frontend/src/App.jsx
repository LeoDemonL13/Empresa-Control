import { Navigate, Route, Routes } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import { RequiereSesion, RequiereRol } from './components/AccessGate'
import Login from './pages/Login'
import Verify2FA from './pages/Verify2FA'
import Inicio from './pages/Inicio'
import Perfil from './pages/Perfil'
import Equipos from './pages/Equipos'
import RedesSociales from './pages/RedesSociales'
import Reportes from './pages/Reportes'
import Usuarios from './pages/Usuarios'
import Bitacora from './pages/Bitacora'
import NotFound from './pages/NotFound'

export default function App() {
  return (
    <>
      <Toaster position="top-right" toastOptions={{ duration: 4000 }} />
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/verificar-2fa" element={<Verify2FA />} />

        <Route element={<RequiereSesion />}>
          <Route element={<Layout />}>
            <Route path="/" element={<Inicio />} />
            <Route path="/perfil" element={<Perfil />} />
            <Route path="/equipos" element={<Equipos />} />
            <Route path="/redes-sociales" element={<RedesSociales />} />
            <Route path="/reportes" element={<Reportes />} />
            <Route path="/bitacora" element={<Bitacora />} />
            <Route element={<RequiereRol roles={['super_admin']} />}>
              <Route path="/administradores" element={<Usuarios />} />
            </Route>
            <Route path="*" element={<NotFound />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </>
  )
}
