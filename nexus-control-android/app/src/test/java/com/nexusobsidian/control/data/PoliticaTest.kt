package com.nexusobsidian.control.data

import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class PoliticaTest {

    @Test
    fun appBloqueadaSiempreBloquea() {
        val politica = Politica("x.exe", "bloqueada", "sin_limite", null, "diario")
        assertTrue(politica.debeBloquear(0))
        assertTrue(politica.debeBloquear(999999))
    }

    @Test
    fun appPermitidaSinLimiteNuncaBloquea() {
        val politica = Politica("y.exe", "permitida", "sin_limite", null, "diario")
        assertFalse(politica.debeBloquear(999999))
    }

    @Test
    fun appConLimiteBloqueaAlAlcanzarloExactamente() {
        val politica = Politica("z.exe", "permitida", "con_limite", 30, "diario")
        assertFalse(politica.debeBloquear(30 * 60 - 1))
        assertTrue(politica.debeBloquear(30 * 60))
        assertTrue(politica.debeBloquear(30 * 60 + 1))
    }

    @Test
    fun appConLimiteSinMinutosDefinidosNoBloquea() {
        val politica = Politica("w.exe", "permitida", "con_limite", null, "diario")
        assertFalse(politica.debeBloquear(999999))
    }

    @Test
    fun appConLimiteCeroNoBloquea() {
        val politica = Politica("v.exe", "permitida", "con_limite", 0, "diario")
        assertFalse(politica.debeBloquear(999999))
    }
}
