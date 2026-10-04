package com.nexusobsidian.control.data

import android.content.Context

class Preferencias(context: Context) {

    private val prefs = context.getSharedPreferences("nexus_credenciales", Context.MODE_PRIVATE)

    var equipoId: Long
        get() = prefs.getLong(CLAVE_EQUIPO_ID, -1L)
        set(value) = prefs.edit().putLong(CLAVE_EQUIPO_ID, value).apply()

    var apiKey: String?
        get() = prefs.getString(CLAVE_API_KEY, null)
        set(value) = prefs.edit().putString(CLAVE_API_KEY, value).apply()

    var apiBaseUrl: String?
        get() = prefs.getString(CLAVE_API_BASE_URL, null)
        set(value) = prefs.edit().putString(CLAVE_API_BASE_URL, value).apply()

    var nombreEquipo: String?
        get() = prefs.getString(CLAVE_NOMBRE_EQUIPO, null)
        set(value) = prefs.edit().putString(CLAVE_NOMBRE_EQUIPO, value).apply()

    val estaEnrolado: Boolean
        get() = equipoId > 0 && !apiKey.isNullOrBlank() && !apiBaseUrl.isNullOrBlank()

    fun guardarEnrolamiento(equipoId: Long, apiKey: String, apiBaseUrl: String, nombreEquipo: String) {
        prefs.edit()
            .putLong(CLAVE_EQUIPO_ID, equipoId)
            .putString(CLAVE_API_KEY, apiKey)
            .putString(CLAVE_API_BASE_URL, apiBaseUrl)
            .putString(CLAVE_NOMBRE_EQUIPO, nombreEquipo)
            .apply()
    }

    fun borrarEnrolamiento() {
        prefs.edit().clear().apply()
    }

    companion object {
        private const val CLAVE_EQUIPO_ID = "equipo_id"
        private const val CLAVE_API_KEY = "api_key"
        private const val CLAVE_API_BASE_URL = "api_base_url"
        private const val CLAVE_NOMBRE_EQUIPO = "nombre_equipo"
    }
}
