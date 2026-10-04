package com.nexusobsidian.control.util

import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import com.nexusobsidian.control.data.AppInstalada

object InventarioApps {

    fun listarAppsVisibles(context: Context): List<AppInstalada> {
        val gestorPaquetes = context.packageManager
        val intentLanzador = Intent(Intent.ACTION_MAIN).addCategory(Intent.CATEGORY_LAUNCHER)

        val candidatos = if (android.os.Build.VERSION.SDK_INT >= 33) {
            gestorPaquetes.queryIntentActivities(
                intentLanzador,
                PackageManager.ResolveInfoFlags.of(0L),
            )
        } else {
            @Suppress("DEPRECATION")
            gestorPaquetes.queryIntentActivities(intentLanzador, 0)
        }

        val propio = context.packageName
        val vistos = mutableSetOf<String>()
        val resultado = mutableListOf<AppInstalada>()

        for (info in candidatos) {
            val paquete = info.activityInfo?.packageName ?: continue
            if (paquete == propio || !vistos.add(paquete)) continue
            val etiqueta = try {
                info.loadLabel(gestorPaquetes)?.toString()
            } catch (e: Exception) {
                null
            } ?: paquete
            resultado.add(AppInstalada(paquete = paquete, etiqueta = etiqueta))
        }

        return resultado.sortedBy { it.etiqueta.lowercase() }
    }
}
