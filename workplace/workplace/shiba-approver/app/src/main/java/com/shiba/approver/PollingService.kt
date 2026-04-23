package com.shiba.approver

import android.app.Service
import android.content.Intent
import android.os.IBinder
import androidx.localbroadcastmanager.content.LocalBroadcastManager
import kotlinx.coroutines.*

class PollingService : Service() {

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private var lastSeenId: String? = null

    companion object {
        const val ACTION_STATUS = "com.shiba.approver.STATUS_UPDATE"
        const val EXTRA_STATE   = "state"
        const val EXTRA_MESSAGE = "message"
    }

    override fun onCreate() {
        super.onCreate()
        NotificationHelper.createChannels(this)
        startForeground(
            NotificationHelper.NOTIF_SERVICE,
            NotificationHelper.buildServiceNotification(this),
        )
        startPolling()
    }

    private fun startPolling() {
        scope.launch {
            while (isActive) {
                try {
                    // Poll approval
                    val pending = ApiClient.fetchPending(applicationContext)
                    if (pending != null && pending.id != lastSeenId) {
                        lastSeenId = pending.id
                        NotificationHelper.showApprovalNotification(applicationContext, pending)
                    }

                    // Poll Shiba status
                    val status = ApiClient.fetchStatus(applicationContext)
                    if (status != null) {
                        val intent = Intent(ACTION_STATUS).apply {
                            putExtra(EXTRA_STATE, status.state)
                            putExtra(EXTRA_MESSAGE, status.message)
                        }
                        LocalBroadcastManager.getInstance(applicationContext).sendBroadcast(intent)
                    }

                } catch (_: Exception) {}
                delay(2_000)
            }
        }
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int =
        START_STICKY

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}
