package com.nexusobsidian.control.ui

import android.content.Intent
import android.content.pm.PackageManager
import android.os.Bundle
import android.os.CountDownTimer
import android.widget.Button
import android.widget.TextView
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import com.nexusobsidian.control.R

class BloqueoActivity : AppCompatActivity() {

    private var cuentaRegresiva: CountDownTimer? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_bloqueo)

        val paquete = intent.getStringExtra(EXTRA_PAQUETE) ?: ""
        val esLimite = intent.getBooleanExtra(EXTRA_ES_LIMITE, false)
        val limiteMinutos = intent.getIntExtra(EXTRA_LIMITE_MINUTOS, 0)
        val etiquetaApp = etiquetaDeApp(paquete)

        val textoTitulo = findViewById<TextView>(R.id.textoTituloBloqueo)
        val textoMensaje = findViewById<TextView>(R.id.textoMensajeBloqueo)
        val textoRegresando = findViewById<TextView>(R.id.textoRegresando)
        val botonVolver = findViewById<Button>(R.id.botonVolverInicio)

        if (esLimite) {
            textoTitulo.text = getString(R.string.bloqueo_titulo_limite)
            textoMensaje.text = getString(R.string.bloqueo_mensaje_limite, etiquetaApp, limiteMinutos)
        } else {
            textoTitulo.text = getString(R.string.bloqueo_titulo_bloqueada)
            textoMensaje.text = getString(R.string.bloqueo_mensaje_bloqueada, etiquetaApp)
        }

        botonVolver.setOnClickListener { irAlInicio() }

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                irAlInicio()
            }
        })

        cuentaRegresiva = object : CountDownTimer(DURACION_AUTO_CIERRE_MS, 1_000L) {
            override fun onTick(restanteMs: Long) {
                val segundos = (restanteMs / 1000).toInt() + 1
                textoRegresando.text = getString(R.string.bloqueo_regresando, segundos)
            }

            override fun onFinish() {
                irAlInicio()
            }
        }.start()
    }

    override fun onDestroy() {
        super.onDestroy()
        cuentaRegresiva?.cancel()
    }

    private fun etiquetaDeApp(paquete: String): String {
        return try {
            val info = packageManager.getApplicationInfo(paquete, 0)
            packageManager.getApplicationLabel(info).toString()
        } catch (e: PackageManager.NameNotFoundException) {
            paquete
        }
    }

    private fun irAlInicio() {
        cuentaRegresiva?.cancel()
        val intentInicio = Intent(Intent.ACTION_MAIN).apply {
            addCategory(Intent.CATEGORY_HOME)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK
        }
        startActivity(intentInicio)
        finish()
    }

    companion object {
        const val EXTRA_PAQUETE = "extra_paquete"
        const val EXTRA_ES_LIMITE = "extra_es_limite"
        const val EXTRA_LIMITE_MINUTOS = "extra_limite_minutos"
        private const val DURACION_AUTO_CIERRE_MS = 6_000L
    }
}
