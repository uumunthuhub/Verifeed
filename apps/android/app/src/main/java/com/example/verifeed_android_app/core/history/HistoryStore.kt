package com.example.verifeed_android_app.core.history

/**
 * Local investigation-history persistence contract (E7).
 *
 * The MVP ships a JSON-file implementation ([FileHistoryStore]); the interface
 * exists so the store can be swapped for a Room DB or a backend-synced store
 * once authentication lands (Phase F).
 */
interface HistoryStore {

    /** Persist a new entry (most recent first). */
    fun add(entry: HistoryEntry)

    /** All entries, newest first. */
    fun entries(): List<HistoryEntry>

    /** Remove every entry (privacy: "Clear history"). */
    fun clear()
}