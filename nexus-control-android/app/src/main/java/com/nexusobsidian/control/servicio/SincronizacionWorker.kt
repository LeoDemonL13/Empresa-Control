package com.nexusobsidian.control.servicio

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import androidx.work.Constraints
import com.nexusobsidian.control.data.Sincronizador
import java.util.concurrent.TimeUnit

class SincronizacionWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val exito = Sincronizador.sincronizar(applicationContext, incluirAppsInstaladas = true)
        return if (exito) Result.success() else Result.retry()
    }

    companion object {
        private const val NOMBRE_TRABAJO_PERIODICO = "nexus_sincronizacion_periodica"
        private const val NOMBRE_TRABAJO_INMEDIATO = "nexus_sincronizacion_inmediata"

        fun programarPeriodico(context: Context) {
            val restricciones = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val solicitud = PeriodicWorkRequestBuilder<SincronizacionWorker>(15, TimeUnit.MINUTES)
                .setConstraints(restricciones)
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                NOMBRE_TRABAJO_PERIODICO,
                ExistingPeriodicWorkPolicy.KEEP,
                solicitud,
            )
        }

        fun cancelar(context: Context) {
            WorkManager.getInstance(context).cancelUniqueWork(NOMBRE_TRABAJO_PERIODICO)
            WorkManager.getInstance(context).cancelUniqueWork(NOMBRE_TRABAJO_INMEDIATO)
        }

        fun ejecutarAhora(context: Context) {
            val restricciones = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val solicitud = OneTimeWorkRequestBuilder<SincronizacionWorker>()
                .setConstraints(restricciones)
                .build()

            WorkManager.getInstance(context).enqueueUniqueWork(
                NOMBRE_TRABAJO_INMEDIATO,
                ExistingWorkPolicy.REPLACE,
                solicitud,
            )
        }
    }
}
