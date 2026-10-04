import { menuParaRol, rutaPermitida } from '../menus'

describe('menú por rol', () => {
  const rutas = (role) => menuParaRol(role).flatMap((g) => g.items.map((i) => i.path))

  it('el súper admin ve Administradores', () => {
    expect(rutas('super_admin')).toContain('/administradores')
  })

  it('el administrador no ve Administradores', () => {
    expect(rutas('admin')).not.toContain('/administradores')
    expect(rutas('admin')).toContain('/equipos')
  })

  it('agrupa por Cuenta, Operación y Administración', () => {
    expect(menuParaRol('super_admin').map((g) => g.label)).toEqual(['Cuenta', 'Operación', 'Administración'])
  })
})

describe('rutaPermitida', () => {
  it('bloquea /administradores a un administrador normal', () => {
    expect(rutaPermitida('admin', '/administradores')).toBe(false)
    expect(rutaPermitida('super_admin', '/administradores')).toBe(true)
  })

  it('permite rutas sin restricción a cualquier rol', () => {
    expect(rutaPermitida('admin', '/bitacora')).toBe(true)
  })
})
