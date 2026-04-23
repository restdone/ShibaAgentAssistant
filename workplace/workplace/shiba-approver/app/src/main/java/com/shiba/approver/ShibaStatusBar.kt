package com.shiba.approver

import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.content.Context
import android.util.AttributeSet
import android.view.Gravity
import android.widget.FrameLayout
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import androidx.core.content.ContextCompat

/**
 * Reusable Shiba status bar.
 * Always visible — shows the Shiba icon with current state.
 *
 * States:
 *   "idle"     → dim icon, gray "Shiba is idle" text, no pulse
 *   "speaking" → bright orange icon, "Speaking…", slow pulse
 *   "working"  → bright orange icon, task label, fast pulse
 */
class ShibaStatusBar @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyle: Int = 0
) : LinearLayout(context, attrs, defStyle) {

    private val iconView: ImageView
    private val statusText: TextView
    private val glowView: android.view.View
    private var pulseAnimator: ObjectAnimator? = null

    init {
        orientation = HORIZONTAL
        gravity = Gravity.CENTER_VERTICAL
        setPadding(32, 20, 32, 20)
        setBackgroundColor(0xFF1A1A1A.toInt())

        // Glow circle behind icon
        val glow = android.view.View(context).apply {
            background = ContextCompat.getDrawable(context, R.drawable.shiba_glow)
            alpha = 0f
        }
        glowView = glow

        val icon = ImageView(context).apply {
            setImageResource(R.mipmap.ic_launcher)
            scaleType = ImageView.ScaleType.CENTER_CROP
            alpha = 0.4f
        }
        iconView = icon

        val label = TextView(context).apply {
            layoutParams = LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f)
            textSize = 13f
            setTextColor(0xFF666666.toInt())
            maxLines = 1
            ellipsize = android.text.TextUtils.TruncateAt.END
            text = "Idle"
        }
        statusText = label

        val iconFrame = FrameLayout(context).apply {
            val size = (56 * resources.displayMetrics.density).toInt()
            layoutParams = LayoutParams(size, size).also { it.marginEnd = (16 * resources.displayMetrics.density).toInt() }
            addView(glow, FrameLayout.LayoutParams(size, size))
            addView(icon, FrameLayout.LayoutParams(size, size))
        }

        addView(iconFrame)
        addView(label)

        // Always visible
        visibility = android.view.View.VISIBLE
    }

    fun update(state: String, message: String) {
        when (state) {
            "speaking" -> showActive("Speaking…", pulseDuration = 1200L)
            "working"  -> showActive(message.ifBlank { "Working…" }, pulseDuration = 600L)
            else       -> showIdle()
        }
    }

    private fun showActive(label: String, pulseDuration: Long) {
        statusText.text = label
        statusText.setTextColor(0xFFFF6B00.toInt())
        iconView.alpha = 1f
        startPulse(pulseDuration)
    }

    private fun showIdle() {
        stopPulse()
        statusText.text = "Idle"
        statusText.setTextColor(0xFF666666.toInt())
        iconView.alpha = 0.4f
    }

    private fun startPulse(duration: Long) {
        stopPulse()
        pulseAnimator = ObjectAnimator.ofFloat(glowView, "alpha", 0f, 0.7f).apply {
            this.duration = duration
            repeatMode = ValueAnimator.REVERSE
            repeatCount = ValueAnimator.INFINITE
            start()
        }
    }

    private fun stopPulse() {
        pulseAnimator?.cancel()
        pulseAnimator = null
        glowView.alpha = 0f
    }
}
