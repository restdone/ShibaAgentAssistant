package com.shiba.approver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import com.google.android.material.bottomnavigation.BottomNavigationView
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

/**
 * Base activity that:
 * 1. Wires the ShibaStatusBar to PollingService broadcasts.
 * 2. Auto-starts the PollingService if a server is configured.
 * 3. Fetches current status immediately on resume (no waiting for next poll).
 * 4. Wires the bottom nav if the layout has one.
 */
abstract class BaseActivity : AppCompatActivity() {

    /** Subclasses set this so the correct nav item stays selected. */
    open val navItemId: Int = R.id.nav_settings

    private val statusReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            val state   = intent.getStringExtra(PollingService.EXTRA_STATE)   ?: "idle"
            val message = intent.getStringExtra(PollingService.EXTRA_MESSAGE) ?: ""
            updateStatusBar(state, message)
        }
    }

    override fun onResume() {
        super.onResume()

        // Register for live broadcasts
        LocalBroadcastManager.getInstance(this).registerReceiver(
            statusReceiver,
            IntentFilter(PollingService.ACTION_STATUS)
        )

        // Auto-start polling service if server is configured
        if (Prefs.getHost(this).isNotBlank()) {
            startForegroundService(Intent(this, PollingService::class.java))
        }

        // Immediately fetch current status so bar is up-to-date on screen open
        lifecycleScope.launch {
            val status = withContext(Dispatchers.IO) {
                try { ApiClient.fetchStatus(this@BaseActivity) } catch (_: Exception) { null }
            }
            if (status != null) {
                updateStatusBar(status.state, status.message)
            }
        }

        // Highlight the correct nav item
        findViewById<BottomNavigationView>(R.id.bottomNav)?.selectedItemId = navItemId
    }

    override fun onPause() {
        super.onPause()
        LocalBroadcastManager.getInstance(this).unregisterReceiver(statusReceiver)
    }

    private fun updateStatusBar(state: String, message: String) {
        findViewById<ShibaStatusBar>(R.id.shibaStatusBar)?.update(state, message)
    }

    /** Wire the bottom nav. Call from onCreate after setContentView. */
    protected fun setupBottomNav() {
        val nav = findViewById<BottomNavigationView>(R.id.bottomNav) ?: return
        nav.selectedItemId = navItemId
        nav.setOnItemSelectedListener { item ->
            if (item.itemId == navItemId) return@setOnItemSelectedListener true
            when (item.itemId) {
                R.id.nav_settings -> {
                    startActivity(Intent(this, MainActivity::class.java).apply {
                        flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
                    })
                    true
                }
                R.id.nav_memory -> {
                    startActivity(Intent(this, MemoryListActivity::class.java).apply {
                        flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
                    })
                    true
                }
                R.id.nav_files -> {
                    startActivity(Intent(this, FilesActivity::class.java).apply {
                        flags = Intent.FLAG_ACTIVITY_CLEAR_TOP or Intent.FLAG_ACTIVITY_SINGLE_TOP
                    })
                    true
                }
                else -> false
            }
        }
    }
}
