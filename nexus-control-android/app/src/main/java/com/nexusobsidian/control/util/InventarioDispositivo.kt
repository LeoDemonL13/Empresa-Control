package com.nexusobsidian.control.util

import android.content.Context
import android.net.ConnectivityManager
import android.net.LinkProperties
import android.net.Network
import android.os.Build
import android.provider.Settings

object InventarioDispositivo {

    fun hostname(context: Context): String {
        val modelo = "${Build.MANUFACTURER} ${Build.MODEL}".trim()
        val idAndroid = try {
            Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID)
        } catch (e: Exception) {
            null
        }
        val sufijo = idAndroid?.takeLast(6) ?: ""
        return if (sufijo.isNotBlank()) "$modelo-$sufijo" else modelo
    }

    fun direccionIp(context: Context): String? {
        return try {
            val conectividad = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            val red: Network = conectividad?.activeNetwork ?: return null
            val propiedades: LinkProperties = conectividad.getLinkProperties(red) ?: return null
            propiedades.linkAddresses
                .map { it.address }
                .firstOrNull { !it.isLoopbackAddress && it.hostAddress?.contains(':') == false }
                ?.hostAddress
        } catch (e: Exception) {
            null
        }
    }

    fun sistemaOperativo(): String = "Android ${Build.VERSION.RELEASE}"
}
