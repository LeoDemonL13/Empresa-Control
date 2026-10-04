package com.nexusobsidian.control.data

data class Politica(
    val ejecutable: String,
    val estado: String,
    val tipoUso: String,
    val limiteMinutos: Int?,
    val periodo: String,
) {
    fun debeBloquear(acumuladoSegundos: Int): Boolean {
        if (estado == ESTADO_BLOQUEADA) return true
        if (tipoUso == TIPO_USO_CON_LIMITE) {
            val limiteSegundos = (limiteMinutos ?: 0) * 60
            if (limiteSegundos > 0 && acumuladoSegundos >= limiteSegundos) return true
        }
        return false
    }

    companion object {
        const val ESTADO_BLOQUEADA = "bloqueada"
        const val ESTADO_PERMITIDA = "permitida"
        const val TIPO_USO_CON_LIMITE = "con_limite"
        const val TIPO_USO_SIN_LIMITE = "sin_limite"
    }
}
