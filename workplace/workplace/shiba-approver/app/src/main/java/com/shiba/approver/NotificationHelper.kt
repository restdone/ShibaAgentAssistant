package com.shiba.approver

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat

object NotificationHelper {

    const val CHANNEL_APPROVAL = "shiba_approval"
    const val CHANNEL_SERVICE  = "shiba_service"
    const val NOTIF_APPROVAL   = 1001
    const val NOTIF_SERVICE    = 1002

    fun createChannels(ctx: Context) {
        val nm = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        nm.createNotificationChannel(
            NotificationChannel(
                CHANNEL_APPROVAL,
                "Shiba Approvals",
                NotificationManager.IMPORTANCE_HIGH,
            ).apply {
                description = "Approval requests from Shiba"
                enableVibration(true)
            }
        )

        nm.createNotificationChannel(
            NotificationChannel(
                CHANNEL_SERVICE,
                "Shiba Polling Service",
                NotificationManager.IMPORTANCE_LOW,
            ).apply {
                description = "Background polling status"
            }
        )
    }

    fun showApprovalNotification(ctx: Context, request: ApiClient.PendingRequest) {
        val intent = Intent(ctx, ApprovalActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("request_id",      request.id)
            putExtra("request_type",    request.type)
            putExtra("request_summary", request.summary)
            putExtra("request_detail",  request.detail)
        }
        val pi = PendingIntent.getActivity(
            ctx, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )

        val notif = NotificationCompat.Builder(ctx, CHANNEL_APPROVAL)
            .setSmallIcon(android.R.drawable.ic_dialog_alert)
            .setContentTitle("Shiba needs approval")
            .setContentText(request.summary)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setAutoCancel(true)
            .setContentIntent(pi)
            .setFullScreenIntent(pi, true)   // show on lock screen
            .build()

        try {
            NotificationManagerCompat.from(ctx).notify(NOTIF_APPROVAL, notif)
        } catch (e: SecurityException) {
            // POST_NOTIFICATIONS permission not granted yet
        }
    }

    fun buildServiceNotification(ctx: Context) =
        NotificationCompat.Builder(ctx, CHANNEL_SERVICE)
            .setSmallIcon(android.R.drawable.ic_menu_send)
            .setContentTitle("Shiba Approver")
            .setContentText("Watching for approval requests…")
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setOngoing(true)
            .build()
}
