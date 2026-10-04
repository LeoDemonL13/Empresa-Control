package com.nexusobsidian.control.ui

import android.content.ComponentName
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.text.TextUtils
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.ProgressBar
import android.widget.TextView
import android.widget.Toast
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.nexusobsidian.control.R
import com.nexusobsidian.control.data.AlmacenEstado
import com.nexusobsidian.control.data.ApiCliente
import com.nexusobsidian.control.data.ErrorApi
import com.nexusobsidian.control.data.Preferencias
import com.nexusobsidian.control.data.Sincronizador
import com.nexusobsidian.control.servicio.MonitorAccesibilidadServicio
import com.nexusobsidian.control.servicio.SincronizacionWorker
import com.nexusobsidian.control.util.InventarioDispositivo
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

class EnrolamientoActivity : AppCompatActivity() {

    private lateinit var preferencias: Preferencias
    private val alcance = CoroutineScope(SupervisorJob() + Dispatchers.Main)

    private lateinit var contenedorEnrolamiento: View
    private lateinit var contenedorEstado: View
    private lateinit var campoServidor: EditText
    private lateinit var campoCodigo: EditText
    private lateinit var textoError: TextView
    private lateinit var botonEnrolar: Button
    private lateinit var barraProgreso: ProgressBar

    private lateinit var textoNombreEquipo: TextView
    private lateinit var textoServidor: TextView
    private lateinit var textoAccesibilidad: TextView
    private lateinit var botonActivarAccesibilidad: Button
    private lateinit var textoBateria: TextView
    private lateinit var botonBateria: Button
    private lateinit var botonSincronizar: Button
    private lateinit var textoEstadoSincronizacion: TextView
    private lateinit var botonDesenrolar: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_enrolamiento)

        preferencias = Preferencias(this)

        contenedorEnrolamiento = findViewById(R.id.contenedorEnrolamiento)
        contenedorEstado = findViewById(R.id.contenedorEstado)
        campoServidor = findViewById(R.id.campoServidor)
        campoCodigo = findViewById(R.id.campoCodigo)
        textoError = findViewById(R.id.textoError)
        botonEnrolar = findViewById(R.id.botonEnrolar)
        barraProgreso = findViewById(R.id.barraProgreso)

        textoNombreEquipo = findViewById(R.id.textoNombreEquipo)
        textoServidor = findViewById(R.id.textoServidor)
        textoAccesibilidad = findViewById(R.id.textoAccesibilidad)
        botonActivarAccesibilidad = findViewById(R.id.botonActivarAccesibilidad)
        textoBateria = findViewById(R.id.textoBateria)
        botonBateria = findViewById(R.id.botonBateria)
        botonSincronizar = findViewById(R.id.botonSincronizar)
        textoEstadoSincronizacion = findViewById(R.id.textoEstadoSincronizacion)
        botonDesenrolar = findViewById(R.id.botonDesenrolar)

        botonEnrolar.setOnClickListener { intentarEnrolar() }
        botonActivarAccesibilidad.setOnClickListener {
            startActivity(Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS))
        }
        botonBateria.setOnClickListener {
            val intent = Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS).apply {
                data = android.net.Uri.parse("package:$packageName")
            }
            startActivity(intent)
        }
        botonSincronizar.setOnClickListener { sincronizarAhora() }
        botonDesenrolar.setOnClickListener { confirmarDesenrolar() }

        actualizarVista()
    }

    override fun onResume() {
        super.onResume()
        actualizarVista()
    }

    override fun onDestroy() {
        super.onDestroy()
        alcance.cancel()
    }

    private fun actualizarVista() {
        if (preferencias.estaEnrolado) {
            contenedorEnrolamiento.visibility = View.GONE
            contenedorEstado.visibility = View.VISIBLE
            textoNombreEquipo.text = getString(R.string.estado_nombre_equipo, preferencias.nombreEquipo ?: "")
            textoServidor.text = getString(R.string.estado_servidor, preferencias.apiBaseUrl ?: "")
            actualizarEstadoAccesibilidad()
            actualizarEstadoBateria()
        } else {
            contenedorEnrolamiento.visibility = View.VISIBLE
            contenedorEstado.visibility = View.GONE
        }
    }

    private fun actualizarEstadoAccesibilidad() {
        if (servicioDeAccesibilidadActivo()) {
            textoAccesibilidad.text = getString(R.string.estado_accesibilidad_activa)
            botonActivarAccesibilidad.visibility = View.GONE
        } else {
            textoAccesibilidad.text = getString(R.string.estado_accesibilidad_pendiente)
            botonActivarAccesibilidad.visibility = View.VISIBLE
        }
    }

    private fun actualizarEstadoBateria() {
        val gestorEnergia = getSystemService(android.os.PowerManager::class.java)
        val yaIgnorada = gestorEnergia?.isIgnoringBatteryOptimizations(packageName) ?: true
        if (yaIgnorada) {
            textoBateria.text = getString(R.string.estado_bateria_activa)
            botonBateria.visibility = View.GONE
        } else {
            textoBateria.text = getString(R.string.estado_bateria_pendiente)
            botonBateria.visibility = View.VISIBLE
        }
    }

    private fun servicioDeAccesibilidadActivo(): Boolean {
        val esperado = ComponentName(this, MonitorAccesibilidadServicio::class.java)
        val habilitados = Settings.Secure.getString(
            contentResolver,
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES,
        ) ?: return false

        val separador = TextUtils.SimpleStringSplitter(':')
        separador.setString(habilitados)
        for (componente in separador) {
            if (ComponentName.unflattenFromString(componente) == esperado) return true
        }
        return false
    }

    private fun intentarEnrolar() {
        val servidor = campoServidor.text.toString().trim().trimEnd('/')
        val codigo = campoCodigo.text.toString().trim().uppercase()

        if (servidor.isEmpty()) {
            mostrarError(getString(R.string.enrol_error_servidor))
            return
        }
        if (codigo.isEmpty()) {
            mostrarError(getString(R.string.enrol_error_codigo))
            return
        }

        ocultarError()
        alternarCargando(true)

        alcance.launch {
            try {
                val cliente = ApiCliente(servidor)
                val resultado = cliente.enrolar(codigo)
                preferencias.guardarEnrolamiento(resultado.equipoId, resultado.apiKey, servidor, resultado.nombre)

                try {
                    ApiCliente(servidor, resultado.equipoId, resultado.apiKey).enviarInventario(
                        hostname = InventarioDispositivo.hostname(this@EnrolamientoActivity),
                        ip = InventarioDispositivo.direccionIp(this@EnrolamientoActivity),
                        sistemaOperativo = InventarioDispositivo.sistemaOperativo(),
                    )
                } catch (e: ErrorApi) {
                }

                SincronizacionWorker.programarPeriodico(this@EnrolamientoActivity)
                SincronizacionWorker.ejecutarAhora(this@EnrolamientoActivity)

                Toast.makeText(
                    this@EnrolamientoActivity,
                    getString(R.string.enrol_exito, resultado.nombre),
                    Toast.LENGTH_LONG,
                ).show()

                actualizarVista()
            } catch (e: ErrorApi) {
                mostrarError(e.message ?: getString(R.string.enrol_error_codigo))
            } finally {
                alternarCargando(false)
            }
        }
    }

    private fun sincronizarAhora() {
        textoEstadoSincronizacion.text = getString(R.string.estado_sincronizando)
        alcance.launch {
            val exito = Sincronizador.sincronizar(this@EnrolamientoActivity, incluirAppsInstaladas = true)
            textoEstadoSincronizacion.text = if (exito) {
                getString(R.string.estado_sincronizado)
            } else {
                getString(R.string.estado_error_sincronizar)
            }
        }
    }

    private fun confirmarDesenrolar() {
        AlertDialog.Builder(this)
            .setTitle(R.string.estado_boton_desenrolar)
            .setMessage(R.string.estado_confirmar_desenrolar)
            .setPositiveButton(android.R.string.ok) { _, _ ->
                preferencias.borrarEnrolamiento()
                AlmacenEstado(this).borrar()
                SincronizacionWorker.cancelar(this)
                campoServidor.setText("")
                campoCodigo.setText("")
                actualizarVista()
            }
            .setNegativeButton(android.R.string.cancel, null)
            .show()
    }

    private fun mostrarError(mensaje: String) {
        textoError.text = mensaje
        textoError.visibility = View.VISIBLE
    }

    private fun ocultarError() {
        textoError.visibility = View.GONE
    }

    private fun alternarCargando(cargando: Boolean) {
        barraProgreso.visibility = if (cargando) View.VISIBLE else View.GONE
        botonEnrolar.isEnabled = !cargando
        botonEnrolar.text = if (cargando) getString(R.string.enrol_enrolando) else getString(R.string.enrol_boton)
    }
}
