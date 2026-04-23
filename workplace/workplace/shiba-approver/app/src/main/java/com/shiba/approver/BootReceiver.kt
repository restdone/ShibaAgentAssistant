package com.shiba.approver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

class BootReceiver : BroadcastReceiver() {
    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            val host = Prefs.getHost(context)
            if (host.isNotBlank()) {
                context.startForegroundService(
                    Intent(context, PollingService::class.java)
                )
            }
        }
    }
}
