package com.nexusobsidian.control.data

import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class CalculoUsoTest {

    @Test
    fun soloEnviaElDeltaNuevoEnCadaCiclo() {
        val estado = EstadoLocal()
        var totalRecibidoPorElServidor = 0

        estado.acumulado["x.exe"] = 60
        estado.sesiones["x.exe"] = 1
        var entradas = CalculoUso.entradasPendientes(estado)
        assertEquals(60, entradas.single().segundos)
        totalRecibidoPorElServidor += entradas.sumOf { it.segundos }
        CalculoUso.confirmarEnvio(estado, entradas)

        estado.acumulado["x.exe"] = 120
        entradas = CalculoUso.entradasPendientes(estado)
        assertEquals(60, entradas.single().segundos)
        totalRecibidoPorElServidor += entradas.sumOf { it.segundos }
        CalculoUso.confirmarEnvio(estado, entradas)

        estado.acumulado["x.exe"] = 180
        entradas = CalculoUso.entradasPendientes(estado)
        assertEquals(60, entradas.single().segundos)
        totalRecibidoPorElServidor += entradas.sumOf { it.segundos }
        CalculoUso.confirmarEnvio(estado, entradas)

        assertEquals(180, totalRecibidoPorElServidor)
    }

    @Test
    fun sinUsoNuevoNoHayNadaQueEnviar() {
        val estado = EstadoLocal()
        estado.acumulado["x.exe"] = 100
        estado.enviado["x.exe"] = 100
        assertTrue(CalculoUso.entradasPendientes(estado).isEmpty())
    }

    @Test
    fun unaNuevaSesionSinTiempoAdicionalSiSeEnvia() {
        val estado = EstadoLocal()
        estado.acumulado["x.exe"] = 100
        estado.enviado["x.exe"] = 100
        estado.sesiones["x.exe"] = 1

        val entradas = CalculoUso.entradasPendientes(estado)
        assertEquals(0, entradas.single().segundos)
        assertEquals(1, entradas.single().sesiones)
    }

    @Test
    fun confirmarEnvioReiniciaLasSesionesPeroNoElAcumulado() {
        val estado = EstadoLocal()
        estado.acumulado["x.exe"] = 90
        estado.sesiones["x.exe"] = 2

        val entradas = CalculoUso.entradasPendientes(estado)
        CalculoUso.confirmarEnvio(estado, entradas)

        assertEquals(90, estado.acumulado["x.exe"])
        assertEquals(90, estado.enviado["x.exe"])
        assertEquals(0, estado.sesiones["x.exe"])
    }
}
