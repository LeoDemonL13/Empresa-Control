package com.nexusobsidian.control.data

import android.content.Context
import com.nexusobsidian.control.util.InventarioApps
import com.nexusobsidian.control.util.InventarioDispositivo

object Sincronizador {

    suspend fun sincronizar(context: Context, incluirAppsInstaladas: Boolean = false): Boolean {
        val preferencias = Preferencias(context)
        if (!preferencias.estaEnrolado) return false

        val apiBaseUrl = preferencias.apiBaseUrl ?: return false
        val cliente = ApiCliente(
            apiBaseUrl = apiBaseUrl,
            equipoId = preferencias.equipoId,
            apiKey = preferencias.apiKey,
        )

        var huboExito = false

        try {
            cliente.enviarInventario(
                hostname = InventarioDispositivo.hostname(context),
                ip = InventarioDispositivo.direccionIp(context),
                sistemaOperativo = InventarioDispositivo.sistemaOperativo(),
            )
            huboExito = true
        } catch (e: ErrorApi) {
        }

        if (incluirAppsInstaladas) {
            try {
                cliente.enviarAppsInstaladas(InventarioApps.listarAppsVisibles(context))
                huboExito = true
            } catch (e: ErrorApi) {
            }
        }

        val almacen = AlmacenEstado(context)

        try {
            val resultado = cliente.obtenerPoliticas()
            val estado = almacen.cargar()
            estado.politicaVersion = resultado.politicaVersion
            estado.politicas.clear()
            for (politica in resultado.politicas) {
                estado.politicas[politica.ejecutable] = politica
            }
            almacen.guardar(estado)
            huboExito = true
        } catch (e: ErrorApi) {
        }

        if (enviarUsoAcumulado(cliente, almacen)) {
            huboExito = true
        }

        return huboExito
    }

    private suspend fun enviarUsoAcumulado(cliente: ApiCliente, almacen: AlmacenEstado): Boolean {
        val estado = almacen.cargar()
        val entradas = CalculoUso.entradasPendientes(estado)
        if (entradas.isEmpty()) return false

        try {
            cliente.enviarUso(estado.fecha, entradas)
        } catch (e: ErrorApi) {
            return false
        }

        CalculoUso.confirmarEnvio(estado, entradas)
        almacen.guardar(estado)
        return true
    }
}
