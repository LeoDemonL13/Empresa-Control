package com.nexusobsidian.control.data

import java.io.BufferedReader
import java.io.InputStreamReader
import java.io.OutputStreamWriter
import java.net.HttpURLConnection
import java.net.URL
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject

class ErrorApi(mensaje: String, val codigoHttp: Int? = null) : Exception(mensaje)

data class ResultadoEnrolamiento(val equipoId: Long, val apiKey: String, val nombre: String)

data class ResultadoPoliticas(val politicaVersion: Int, val politicas: List<Politica>)

data class EntradaUso(val ejecutable: String, val segundos: Int, val sesiones: Int)

data class AppInstalada(val paquete: String, val etiqueta: String)

class ApiCliente(
    private val apiBaseUrl: String,
    private val equipoId: Long = -1L,
    private val apiKey: String? = null,
) {

    private val base: String = apiBaseUrl.trimEnd('/')

    suspend fun enrolar(codigo: String): ResultadoEnrolamiento = withContext(Dispatchers.IO) {
        val cuerpo = JSONObject().put("codigo", codigo)
        val respuesta = peticion("POST", "/api/agente/enrolar", cuerpo, conCredenciales = false)
        ResultadoEnrolamiento(
            equipoId = respuesta.getLong("equipo_id"),
            apiKey = respuesta.getString("api_key"),
            nombre = respuesta.getString("nombre"),
        )
    }

    suspend fun enviarInventario(hostname: String, ip: String?, sistemaOperativo: String) = withContext(Dispatchers.IO) {
        val cuerpo = JSONObject()
        cuerpo.put("hostname", hostname)
        cuerpo.put("ip", ip ?: "")
        cuerpo.put("sistema_operativo", sistemaOperativo)
        peticion("POST", "/api/agente/inventario", cuerpo, conCredenciales = true)
        Unit
    }

    suspend fun enviarAppsInstaladas(apps: List<AppInstalada>) = withContext(Dispatchers.IO) {
        val lista = JSONArray()
        for (app in apps) {
            val item = JSONObject()
            item.put("paquete", app.paquete)
            item.put("etiqueta", app.etiqueta)
            lista.put(item)
        }
        val cuerpo = JSONObject().put("apps", lista)
        peticion("POST", "/api/agente/apps-instaladas", cuerpo, conCredenciales = true)
        Unit
    }

    suspend fun obtenerPoliticas(): ResultadoPoliticas = withContext(Dispatchers.IO) {
        val respuesta = peticion("GET", "/api/agente/politicas", null, conCredenciales = true)
        val politicas = mutableListOf<Politica>()
        val lista = respuesta.getJSONArray("politicas")
        for (i in 0 until lista.length()) {
            val p = lista.getJSONObject(i)
            politicas.add(
                Politica(
                    ejecutable = p.getString("ejecutable"),
                    estado = p.getString("estado"),
                    tipoUso = p.getString("tipo_uso"),
                    limiteMinutos = if (p.isNull("limite_minutos")) null else p.optInt("limite_minutos"),
                    periodo = p.optString("periodo", "diario"),
                ),
            )
        }
        ResultadoPoliticas(respuesta.getInt("politica_version"), politicas)
    }

    suspend fun enviarUso(fecha: String, entradas: List<EntradaUso>) = withContext(Dispatchers.IO) {
        val lista = JSONArray()
        for (entrada in entradas) {
            val item = JSONObject()
            item.put("ejecutable", entrada.ejecutable)
            item.put("segundos", entrada.segundos)
            item.put("sesiones", entrada.sesiones)
            lista.put(item)
        }
        val cuerpo = JSONObject()
        cuerpo.put("fecha", fecha)
        cuerpo.put("entradas", lista)
        peticion("POST", "/api/agente/uso", cuerpo, conCredenciales = true)
        Unit
    }

    private fun peticion(metodo: String, ruta: String, cuerpo: JSONObject?, conCredenciales: Boolean): JSONObject {
        val conexion = URL(base + ruta).openConnection() as HttpURLConnection
        try {
            conexion.requestMethod = metodo
            conexion.connectTimeout = 10_000
            conexion.readTimeout = 10_000
            conexion.setRequestProperty("Content-Type", "application/json; charset=utf-8")
            conexion.setRequestProperty("Accept", "application/json")

            if (conCredenciales) {
                conexion.setRequestProperty("X-Device-Id", equipoId.toString())
                conexion.setRequestProperty("X-Api-Key", apiKey ?: "")
            }

            if (cuerpo != null) {
                conexion.doOutput = true
                OutputStreamWriter(conexion.outputStream, Charsets.UTF_8).use { escritor ->
                    escritor.write(cuerpo.toString())
                }
            }

            val codigo = conexion.responseCode
            val flujo = if (codigo in 200..299) conexion.inputStream else conexion.errorStream
            val texto = flujo?.let { leerTexto(it) } ?: ""

            if (codigo !in 200..299) {
                val mensaje = try {
                    JSONObject(texto).optString("error", "Error HTTP $codigo")
                } catch (e: Exception) {
                    "Error HTTP $codigo"
                }
                throw ErrorApi(mensaje, codigo)
            }

            return if (texto.isBlank()) JSONObject() else JSONObject(texto)
        } catch (e: ErrorApi) {
            throw e
        } catch (e: Exception) {
            throw ErrorApi("No se pudo contactar al servidor: ${e.message}")
        } finally {
            conexion.disconnect()
        }
    }

    private fun leerTexto(flujo: java.io.InputStream): String {
        BufferedReader(InputStreamReader(flujo, Charsets.UTF_8)).use { lector ->
            return lector.readText()
        }
    }
}
