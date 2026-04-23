package com.shiba.approver

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.lifecycle.lifecycleScope
import com.shiba.approver.databinding.ActivityMainBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

class MainActivity : BaseActivity() {

    override val navItemId = R.id.nav_settings

    private lateinit var binding: ActivityMainBinding

    private val notifPermission = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* result handled silently */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        // Ask for notification permission on Android 13+
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED
            ) {
                notifPermission.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        // Restore saved values
        binding.etHost.setText(Prefs.getHost(this))
        binding.etPort.setText(Prefs.getPort(this))

        binding.btnSave.setOnClickListener {
            val host = binding.etHost.text.toString().trim()
            val port = binding.etPort.text.toString().trim()
            if (host.isBlank()) {
                Toast.makeText(this, "Enter the server IP address", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            Prefs.save(this, host, port)
            Toast.makeText(this, "Saved", Toast.LENGTH_SHORT).show()
        }

        binding.btnTest.setOnClickListener {
            val host = binding.etHost.text.toString().trim()
            val port = binding.etPort.text.toString().trim()
            if (host.isBlank()) {
                Toast.makeText(this, "Enter the server IP first", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            Prefs.save(this, host, port)
            appendDebug("Testing connection…")
            binding.tvStatus.text = "Testing…"
            lifecycleScope.launch {
                val result = withContext(Dispatchers.IO) { ApiClient.pingWithDetail(this@MainActivity) }
                val success = result.startsWith("OK")
                binding.tvStatus.text = if (success) "Connected" else "Could not reach server"
                appendDebug("Result: $result")
            }
        }

        binding.btnStart.setOnClickListener {
            val host = Prefs.getHost(this)
            if (host.isBlank()) {
                Toast.makeText(this, "Save a server address first", Toast.LENGTH_SHORT).show()
                return@setOnClickListener
            }
            startForegroundService(android.content.Intent(this, PollingService::class.java))
            binding.tvStatus.text = "Polling started"
        }

        binding.btnStop.setOnClickListener {
            stopService(android.content.Intent(this, PollingService::class.java))
            binding.tvStatus.text = "Polling stopped"
        }

        binding.btnClearLog.setOnClickListener {
            binding.tvDebugLog.text = ""
        }

        setupBottomNav()
    }

    private fun appendDebug(line: String) {
        val current = binding.tvDebugLog.text.toString()
        val updated = if (current.isBlank()) line else "$current\n$line"
        binding.tvDebugLog.text = updated
        binding.scrollDebugLog.post {
            binding.scrollDebugLog.fullScroll(android.view.View.FOCUS_DOWN)
        }
    }
}
