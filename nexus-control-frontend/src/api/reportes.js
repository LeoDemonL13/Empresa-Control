import api from './axios'

function nombreDesdeCabecera(cabecera, alterno) {
  const match = /filename="?([^";]+)"?/.exec(cabecera || '')
  return match ? match[1] : alterno
}

function descargar(blob, nombre) {
  const url = window.URL.createObjectURL(blob)
  const enlace = document.createElement('a')
  enlace.href = url
  enlace.download = nombre
  document.body.appendChild(enlace)
  enlace.click()
  enlace.remove()
  window.URL.revokeObjectURL(url)
}

async function pedirYDescargar(ruta, params, alterno) {
  const respuesta = await api.get(ruta, { params, responseType: 'blob' })
  const nombre = nombreDesdeCabecera(respuesta.headers['content-disposition'], alterno)
  descargar(respuesta.data, nombre)
}

export function descargarReporteGeneral(formato) {
  return pedirYDescargar('/reportes/general', { formato }, `reporte-general.${formato}`)
}

export function descargarReporteUso(params) {
  return pedirYDescargar('/reportes/uso', params, `reporte-uso.${params.formato}`)
}

export function descargarReporteAuditoria(params) {
  return pedirYDescargar('/reportes/auditoria', params, `reporte-auditoria.${params.formato}`)
}

export async function extraerErrorDeBlob(err) {
  const datos = err?.response?.data
  if (!(datos instanceof Blob)) return err.response?.data?.error
  try {
    const texto = await datos.text()
    return JSON.parse(texto).error
  } catch {
    return undefined
  }
}
