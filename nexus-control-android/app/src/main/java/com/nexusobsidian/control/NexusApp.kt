package com.nexusobsidian.control

import android.app.Application
import com.nexusobsidian.control.data.Preferencias
import com.nexusobsidian.control.servicio.SincronizacionWorker

class NexusApp : Application() {
    override fun onCreate() {
        super.onCreate()
        if (Preferencias(this).estaEnrolado) {
            SincronizacionWorker.programarPeriodico(this)
        }
    }
}
