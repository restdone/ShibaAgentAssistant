package com.shiba.approver

import android.content.Context
import android.util.Log
import com.google.gson.Gson
import com.google.gson.JsonObject
import com.google.gson.reflect.TypeToken
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

object ApiClient {

    private const val TAG = "ShibaApiClient"

    private val client = OkHttpClient.Builder()
        .connectTimeout(5, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()

    private val gson = Gson()
    private val JSON = "application/json; charset=utf-8".toMediaType()

    // ── Approval ─────────────────────────────────────────────────────────────

    data class PendingRequest(
        val id: String,
        val type: String,
        val summary: String,
        val detail: String,
        val created_at: String,
    )

    data class ShibaStatus(
        val state: String,   // "idle" | "speaking" | "working"
        val message: String,
    )

    /** Returns the pending request, or null if none / server unreachable. */
    fun fetchPending(ctx: Context): PendingRequest? {
        val url = "${Prefs.baseUrl(ctx)}/approval/pending"
        Log.d(TAG, "fetchPending → $url")
        return try {
            val req = Request.Builder().url(url).get().build()
            val resp = client.newCall(req).execute()
            Log.d(TAG, "fetchPending ← ${resp.code}")
            if (resp.code == 204) return null
            val body = resp.body?.string() ?: return null
            gson.fromJson(body, PendingRequest::class.java)
        } catch (e: Exception) {
            Log.e(TAG, "fetchPending error: ${e::class.simpleName}: ${e.message}", e)
            null
        }
    }

    /** Fetch Shiba's current status for the status bar. Returns null on failure. */
    fun fetchStatus(ctx: Context): ShibaStatus? {
        val url = "${Prefs.baseUrl(ctx)}/status"
        return try {
            val req = Request.Builder().url(url).get().build()
            val resp = client.newCall(req).execute()
            if (!resp.isSuccessful) return null
            val body = resp.body?.string() ?: return null
            val obj = gson.fromJson(body, JsonObject::class.java)
            ShibaStatus(
                state = obj.get("state")?.asString ?: "idle",
                message = obj.get("message")?.asString ?: "",
            )
        } catch (e: Exception) {
            null
        }
    }

    /** Send approve/reject decision. Returns true on success. */
    fun respond(ctx: Context, id: String, approved: Boolean): Boolean {
        val url = "${Prefs.baseUrl(ctx)}/approval/respond"
        Log.d(TAG, "respond → $url  id=$id  approved=$approved")
        return try {
            val json = JsonObject().apply {
                addProperty("id", id)
                addProperty("approved", approved)
            }
            val body = gson.toJson(json).toRequestBody(JSON)
            val req = Request.Builder().url(url).post(body).build()
            val resp = client.newCall(req).execute()
            Log.d(TAG, "respond ← ${resp.code}")
            resp.isSuccessful
        } catch (e: Exception) {
            Log.e(TAG, "respond error: ${e::class.simpleName}: ${e.message}", e)
            false
        }
    }

    /**
     * Ping the server. Returns a human-readable result string for display.
     * Success: "OK — HTTP 200"
     * Failure: the exception class and message.
     */
    fun pingWithDetail(ctx: Context): String {
        val url = "${Prefs.baseUrl(ctx)}/ping"
        Log.d(TAG, "ping → $url")
        return try {
            val req = Request.Builder().url(url).get().build()
            val resp = client.newCall(req).execute()
            val code = resp.code
            Log.d(TAG, "ping ← $code")
            if (resp.isSuccessful) "OK — HTTP $code" else "Server returned HTTP $code"
        } catch (e: Exception) {
            val msg = "${e::class.java.simpleName}: ${e.message}"
            Log.e(TAG, "ping error: $msg", e)
            msg
        }
    }

    /** Kept for backward compatibility. */
    fun ping(ctx: Context): Boolean = pingWithDetail(ctx).startsWith("OK")

    // ── Vault ─────────────────────────────────────────────────────────────────

    /**
     * Fetch the list of note names from /vault/list.
     * Returns an empty list on failure.
     */
    fun fetchVaultList(ctx: Context): List<String> {
        val url = "${Prefs.baseUrl(ctx)}/vault/list"
        Log.d(TAG, "fetchVaultList → $url")
        return try {
            val req = Request.Builder().url(url).get().build()
            val resp = client.newCall(req).execute()
            Log.d(TAG, "fetchVaultList ← ${resp.code}")
            if (!resp.isSuccessful) return emptyList()
            val body = resp.body?.string() ?: return emptyList()
            val obj = gson.fromJson(body, JsonObject::class.java)
            val arr = obj.getAsJsonArray("notes") ?: return emptyList()
            val type = object : TypeToken<List<String>>() {}.type
            gson.fromJson(arr, type)
        } catch (e: Exception) {
            Log.e(TAG, "fetchVaultList error: ${e.message}", e)
            emptyList()
        }
    }

    /**
     * Fetch the content of a single note by name.
     * Returns null on failure.
     */
    fun fetchVaultNote(ctx: Context, noteName: String): String? {
        val encodedName = java.net.URLEncoder.encode(noteName, "UTF-8")
        val url = "${Prefs.baseUrl(ctx)}/vault/read?note=$encodedName"
        Log.d(TAG, "fetchVaultNote → $url")
        return try {
            val req = Request.Builder().url(url).get().build()
            val resp = client.newCall(req).execute()
            Log.d(TAG, "fetchVaultNote ← ${resp.code}")
            if (!resp.isSuccessful) return null
            val body = resp.body?.string() ?: return null
            val obj = gson.fromJson(body, JsonObject::class.java)
            obj.get("content")?.asString
        } catch (e: Exception) {
            Log.e(TAG, "fetchVaultNote error: ${e.message}", e)
            null
        }
    }
}
