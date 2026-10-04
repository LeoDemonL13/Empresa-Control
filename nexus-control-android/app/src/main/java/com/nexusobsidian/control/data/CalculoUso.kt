package com.nexusobsidian.control.data

object CalculoUso {

    fun entradasPendientes(estado: EstadoLocal): List<EntradaUso> {
        val entradas = mutableListOf<EntradaUso>()
        for ((ejecutable, segundos) in estado.acumulado) {
            val enviadoPrevio = estado.enviado[ejecutable] ?: 0
            val delta = (segundos - enviadoPrevio).coerceAtLeast(0)
            val sesiones = estado.sesiones[ejecutable] ?: 0
            if (delta == 0 && sesiones == 0) continue
            entradas.add(EntradaUso(ejecutable, delta, sesiones))
        }
        return entradas
    }

    fun confirmarEnvio(estado: EstadoLocal, entradas: List<EntradaUso>) {
        for (entrada in entradas) {
            estado.enviado[entrada.ejecutable] = estado.acumulado[entrada.ejecutable] ?: 0
            estado.sesiones[entrada.ejecutable] = 0
        }
    }
}
