package com.example.verifeed_android_app.core.screening

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import androidx.core.app.NotificationCompat
import com.example.verifeed_android_app.MainActivity
import com.example.verifeed_android_app.core.model.RiskLevel

/**
 * Opt-in Notification Screening Service (Phase F Scaffolding).
 *
 * Adheres strictly to Privacy & Permission Strategy (§78.5) and Mobile Quality Gates (§78.11):
 * 1. Only active when user grants Notification Access in Android Settings AND enables the toggle in VeriFeed settings.
 * 2. Filters notifications to target messaging/communication packages only.
 * 3. Runs local Stage 1 screening (no external API calls for raw notification text).
 * 4. Raises an in-app alert when high-risk phishing/scam signals are detected.
 */
class VeriFeedNotificationListener : NotificationListenerService() {

    private val localEngine by lazy { LocalScreeningEngine() }

    override fun onNotificationPosted(sbn: StatusBarNotification?) {
        super.onNotificationPosted(sbn)
        if (sbn == null) return

        val packageName = sbn.packageName ?: return
        if (!isMonitoredPackage(packageName)) return

        val extras = sbn.notification?.extras ?: return
        val title = extras.getCharSequence("android.title")?.toString() ?: ""
        val text = extras.getCharSequence("android.text")?.toString() ?: ""

        val combinedContent = "$title $text".trim()
        if (combinedContent.isBlank()) return

        // Local Stage 1 Screening — zero network transmission
        val result = localEngine.screen(combinedContent)
        if (result.riskLevel == RiskLevel.HIGH) {
            sendSuspiciousAlert(packageName, combinedContent, result.signals.map { it.description })
        }
    }

    private fun isMonitoredPackage(pkg: String): Boolean {
        val targetPackages = setOf(
            "com.google.android.apps.messaging", // Standard Android Messages
            "com.whatsapp",                      // WhatsApp
            "com.google.android.gm",             // Gmail
            "org.telegram.messenger"             // Telegram
        )
        return targetPackages.contains(pkg) || pkg.contains("sms") || pkg.contains("message")
    }

    private fun sendSuspiciousAlert(pkg: String, snippet: String, signals: List<String>) {
        val channelId = "verifeed_alerts"
        val notificationManager = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager ?: return

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                channelId,
                "VeriFeed Protection Alerts",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Alerts when suspicious messages or URLs are intercepted"
            }
            notificationManager.createNotificationChannel(channel)
        }

        val intent = Intent(this, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            putExtra("shared_text", snippet)
        }

        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val alertText = if (signals.isNotEmpty()) signals.first() else "Suspicious signals detected in message"

        val builder = NotificationCompat.Builder(this, channelId)
            .setSmallIcon(android.R.drawable.stat_notify_error)
            .setContentTitle("⚠️ VeriFeed Suspicious Alert")
            .setContentText(alertText)
            .setStyle(NotificationCompat.BigTextStyle().bigText("Detected in $pkg:\n$alertText\n\nTap to verify safely with VeriFeed."))
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)

        notificationManager.notify(pkg.hashCode(), builder.build())
    }
}
