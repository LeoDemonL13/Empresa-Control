import api from './axios'

export function listarCategorias() {
  return api.get('/categorias').then((r) => r.data)
}
