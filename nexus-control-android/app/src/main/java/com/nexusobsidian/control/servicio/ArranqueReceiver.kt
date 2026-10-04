package com.nexusobsidian.control.servicio

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

class ArranqueReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent?) {
        if (intent?.action != Intent.ACTION_BOOT_COMPLETED) return
        SincronizacionWorker.programarPeriodico(context)
    }
}
