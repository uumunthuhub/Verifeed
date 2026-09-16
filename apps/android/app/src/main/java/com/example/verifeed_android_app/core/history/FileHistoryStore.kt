package com.example.verifeed_android_app.core.history

import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/**
 * JSON-file-backed [HistoryStore] (E7).
 *
 * Persists a capped list of entries to `history.json` inside the supplied
 * directory. Thread-safe via a private lock. The format is deliberately simple
 * (JSON array of [HistoryEntry] objects) so a future Room migration can seed
 * its tables from the same file.
 */
class FileHistoryStore(
    private val directory: File,
    private val maxEntries: Int = 50,
) : HistoryStore {

    private val lock = Object()
    private val historyFile: File get() = File(directory, "history.json")

    override fun add(entry: HistoryEntry) {
        synchronized(lock) {
            val updated = (listOf(entry) + readAllLocked()).take(maxEntries)
            writeLocked(updated)
        }
    }

    override fun entries(): List<HistoryEntry> {
        synchronized(lock) {
            return readAllLocked()
        }
    }

    override fun clear() {
        synchronized(lock) {
            historyFile.delete() // file recreated lazily on next add
        }
    }

    // ------------------------------------------------------------------
    // Internals (caller must hold the lock)
    // ------------------------------------------------------------------

    private fun readAllLocked(): List<HistoryEntry> {
        if (!historyFile.exists()) return emptyList()
        return try {
            val array = JSONArray(historyFile.readText())
            (0 until array.length()).map { i -> HistoryEntry.fromJson(array.getJSONObject(i)) }
        } catch (e: Exception) {
            // Corrupt localStorage JSON should never crash the app — treat as empty.
            emptyList()
        }
    }

    private fun writeLocked(entries: List<HistoryEntry>) {
        directory.mkdirs()
        val array = JSONArray()
        entries.forEach { entry -> array.put(HistoryEntry.toJson(entry)) }
        historyFile.writeText(array.toString())
    }
}