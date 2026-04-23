package com.shiba.approver

import android.content.Context

object Prefs {
    private const val FILE = "shiba_prefs"
    private const val KEY_HOST = "server_host"
    private const val KEY_PORT = "server_port"
    private const val DEFAULT_PORT = "7845"

    fun getHost(ctx: Context): String =
        ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE)
            .getString(KEY_HOST, "") ?: ""

    fun getPort(ctx: Context): String =
        ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE)
            .getString(KEY_PORT, DEFAULT_PORT) ?: DEFAULT_PORT

    fun save(ctx: Context, host: String, port: String) {
        ctx.getSharedPreferences(FILE, Context.MODE_PRIVATE).edit()
            .putString(KEY_HOST, host.trim())
            .putString(KEY_PORT, port.trim())
            .apply()
    }

    fun baseUrl(ctx: Context): String {
        val host = getHost(ctx)
        val port = getPort(ctx)
        return "http://$host:$port"
    }
}
