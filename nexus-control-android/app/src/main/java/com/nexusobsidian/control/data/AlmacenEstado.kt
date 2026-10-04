package com.nexusobsidian.control.data

import android.content.Context
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import org.json.JSONObject

class EstadoLocal(
    var politicaVersion: Int = 0,
    val politicas: MutableMap<String, Politica> = mutableMapOf(),
    var fecha: String = fechaDeHoy(),
    val acumulado: MutableMap<String, Int> = mutableMapOf(),
    val enviado: MutableMap<String, Int> = mutableMapOf(),
    val sesiones: MutableMap<String, Int> = mutableMapOf(),
) {
    companion object {
        fun fechaDeHoy(): String =
            SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())
    }
}

class AlmacenEstado(context: Context) {

    private val prefs = context.getSharedPreferences("nexus_estado", Context.MODE_PRIVATE)

    @Synchronized
    fun cargar(): EstadoLocal {
        val crudo = prefs.getString(CLAVE_ESTADO, null) ?: return EstadoLocal()
        val estado = try {
            deserializar(crudo)
        } catch (e: Exception) {
            EstadoLocal()
        }

        val hoy = EstadoLocal.fechaDeHoy()
        if (estado.fecha != hoy) {
            estado.fecha = hoy
            estado.acumulado.clear()
            estado.enviado.clear()
            estado.sesiones.clear()
        }
        return estado
    }

    @Synchronized
    fun guardar(estado: EstadoLocal) {
        prefs.edit().putString(CLAVE_ESTADO, serializar(estado)).apply()
    }

    @Synchronized
    fun borrar() {
        prefs.edit().clear().apply()
    }

    private fun serializar(estado: EstadoLocal): String {
        val raiz = JSONObject()
        raiz.put("politica_version", estado.politicaVersion)
        raiz.put("fecha", estado.fecha)

        val politicasJson = JSONObject()
        for ((ejecutable, politica) in estado.politicas) {
            val p = JSONObject()
            p.put("estado", politica.estado)
            p.put("tipo_uso", politica.tipoUso)
            p.put("limite_minutos", politica.limiteMinutos ?: JSONObject.NULL)
            p.put("periodo", politica.periodo)
            politicasJson.put(ejecutable, p)
        }
        raiz.put("politicas", politicasJson)

        val acumuladoJson = JSONObject()
        for ((ejecutable, segundos) in estado.acumulado) acumuladoJson.put(ejecutable, segundos)
        raiz.put("acumulado", acumuladoJson)

        val enviadoJson = JSONObject()
        for ((ejecutable, segundos) in estado.enviado) enviadoJson.put(ejecutable, segundos)
        raiz.put("enviado", enviadoJson)

        val sesionesJson = JSONObject()
        for ((ejecutable, cuenta) in estado.sesiones) sesionesJson.put(ejecutable, cuenta)
        raiz.put("sesiones", sesionesJson)

        return raiz.toString()
    }

    private fun deserializar(crudo: String): EstadoLocal {
        val raiz = JSONObject(crudo)
        val estado = EstadoLocal(
            politicaVersion = raiz.optInt("politica_version", 0),
            fecha = raiz.optString("fecha", EstadoLocal.fechaDeHoy()),
        )

        val politicasJson = raiz.optJSONObject("politicas")
        if (politicasJson != null) {
            for (ejecutable in politicasJson.keys()) {
                val p = politicasJson.getJSONObject(ejecutable)
                estado.politicas[ejecutable] = Politica(
                    ejecutable = ejecutable,
                    estado = p.optString("estado", Politica.ESTADO_PERMITIDA),
                    tipoUso = p.optString("tipo_uso", Politica.TIPO_USO_SIN_LIMITE),
                    limiteMinutos = if (p.isNull("limite_minutos")) null else p.optInt("limite_minutos"),
                    periodo = p.optString("periodo", "diario"),
                )
            }
        }

        val acumuladoJson = raiz.optJSONObject("acumulado")
        if (acumuladoJson != null) {
            for (ejecutable in acumuladoJson.keys()) {
                estado.acumulado[ejecutable] = acumuladoJson.optInt(ejecutable, 0)
            }
        }

        val enviadoJson = raiz.optJSONObject("enviado")
        if (enviadoJson != null) {
            for (ejecutable in enviadoJson.keys()) {
                estado.enviado[ejecutable] = enviadoJson.optInt(ejecutable, 0)
            }
        }

        val sesionesJson = raiz.optJSONObject("sesiones")
        if (sesionesJson != null) {
            for (ejecutable in sesionesJson.keys()) {
                estado.sesiones[ejecutable] = sesionesJson.optInt(ejecutable, 0)
            }
        }

        return estado
    }

    companion object {
        private const val CLAVE_ESTADO = "estado_json"
    }
}
