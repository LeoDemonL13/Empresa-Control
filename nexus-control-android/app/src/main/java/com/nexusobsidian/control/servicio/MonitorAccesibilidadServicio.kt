package com.nexusobsidian.control.servicio

import android.accessibilityservice.AccessibilityService
import android.content.Intent
import android.os.Handler
import android.os.Looper
import android.view.accessibility.AccessibilityEvent
import com.nexusobsidian.control.data.AlmacenEstado
import com.nexusobsidian.control.data.Politica
import com.nexusobsidian.control.data.Sincronizador
import com.nexusobsidian.control.ui.BloqueoActivity
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

class MonitorAccesibilidadServicio : AccessibilityService() {

    private lateinit var almacen: AlmacenEstado
    private val manejador = Handler(Looper.getMainLooper())
    private val alcanceServicio = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    private var paqueteActual: String? = null
    private var inicioSegmentoMillis: Long = 0L
    private var paqueteBloqueadoMostrado: String? = null
    private var sincronizandoEnEsteMomento = false
    private var tics = 0

    private val tareaPeriodica = object : Runnable {
        override fun run() {
            revisarSegmentoActual()
            tics += 1
            if (tics % TICS_POR_SINCRONIA == 0) {
                sincronizarEnSegundoPlano()
            }
            manejador.postDelayed(this, INTERVALO_REVISION_MS)
        }
    }

    override fun onServiceConnected() {
        super.onServiceConnected()
        almacen = AlmacenEstado(applicationContext)
        manejador.removeCallbacks(tareaPeriodica)
        manejador.postDelayed(tareaPeriodica, INTERVALO_REVISION_MS)
        sincronizarEnSegundoPlano()
    }

    private fun sincronizarEnSegundoPlano() {
        if (sincronizandoEnEsteMomento) return
        sincronizandoEnEsteMomento = true
        alcanceServicio.launch {
            try {
                Sincronizador.sincronizar(applicationContext)
            } finally {
                sincronizandoEnEsteMomento = false
            }
        }
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        if (event == null) return
        if (event.eventType != AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) return

        val paquete = event.packageName?.toString() ?: return
        if (paquete == packageName) return
        if (paquete == paqueteActual) return

        cerrarSegmentoActual()

        paqueteActual = paquete
        inicioSegmentoMillis = System.currentTimeMillis()
        paqueteBloqueadoMostrado = null

        val estado = almacen.cargar()
        estado.sesiones[paquete] = (estado.sesiones[paquete] ?: 0) + 1
        almacen.guardar(estado)

        evaluarBloqueo(paquete)
    }

    override fun onInterrupt() {
    }

    override fun onDestroy() {
        super.onDestroy()
        cerrarSegmentoActual()
        manejador.removeCallbacks(tareaPeriodica)
        alcanceServicio.cancel()
    }

    private fun cerrarSegmentoActual() {
        val paquete = paqueteActual ?: return
        if (!::almacen.isInitialized) return
        val segundos = segundosTranscurridosYReiniciar()
        if (segundos <= 0) return

        val estado = almacen.cargar()
        estado.acumulado[paquete] = (estado.acumulado[paquete] ?: 0) + segundos
        almacen.guardar(estado)
    }

    private fun revisarSegmentoActual() {
        val paquete = paqueteActual ?: return
        if (!::almacen.isInitialized) return
        val segundos = segundosTranscurridosYReiniciar()
        if (segundos <= 0) return

        val estado = almacen.cargar()
        estado.acumulado[paquete] = (estado.acumulado[paquete] ?: 0) + segundos
        almacen.guardar(estado)

        evaluarBloqueo(paquete)
    }

    private fun segundosTranscurridosYReiniciar(): Int {
        val ahora = System.currentTimeMillis()
        val transcurridoMs = ahora - inicioSegmentoMillis
        inicioSegmentoMillis = ahora
        if (transcurridoMs <= 0) return 0
        return (transcurridoMs / 1000).toInt()
    }

    private fun evaluarBloqueo(paquete: String) {
        if (paquete == paqueteBloqueadoMostrado) return

        val estado = almacen.cargar()
        val politica = estado.politicas[paquete] ?: return
        val acumuladoSegundos = estado.acumulado[paquete] ?: 0
        if (!politica.debeBloquear(acumuladoSegundos)) return

        paqueteBloqueadoMostrado = paquete
        mostrarBloqueo(paquete, politica, acumuladoSegundos)
    }

    private fun mostrarBloqueo(paquete: String, politica: Politica, acumuladoSegundos: Int) {
        val esPorLimite = politica.estado != Politica.ESTADO_BLOQUEADA &&
            politica.tipoUso == Politica.TIPO_USO_CON_LIMITE

        val intent = Intent(this, BloqueoActivity::class.java).apply {
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            putExtra(BloqueoActivity.EXTRA_PAQUETE, paquete)
            putExtra(BloqueoActivity.EXTRA_ES_LIMITE, esPorLimite)
            putExtra(BloqueoActivity.EXTRA_LIMITE_MINUTOS, politica.limiteMinutos ?: (acumuladoSegundos / 60))
        }
        startActivity(intent)
    }

    companion object {
        private const val INTERVALO_REVISION_MS = 20_000L
        private const val TICS_POR_SINCRONIA = 3
    }
}
