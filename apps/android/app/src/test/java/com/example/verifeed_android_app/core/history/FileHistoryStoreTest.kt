package com.example.verifeed_android_app.core.history

import java.io.File
import org.junit.Test
import org.junit.Assert.*

/**
 * Local investigation history (E7) — JSON round-trip, ordering, cap and
 * corruption tolerance.
 */
class FileHistoryStoreTest {

    private fun tempStore(): FileHistoryStore {
        val dir = File(java.nio.file.Files.createTempDirectory("verifeed-history-test").toFile(), "history")
        return FileHistoryStore(dir)
    }

    @Test
    fun persistsAndLoadsEntry() {
        val store = tempStore()
        store.add(HistoryEntry.fromScreening("Congratulations, you won!", "HIGH"))

        val loaded = store.entries()
        assertEquals(1, loaded.size)
        assertEquals("Congratulations, you won!", loaded[0].query)
        assertEquals("HIGH", loaded[0].riskLevel)
    }

    @Test
    fun newestEntryFirst() {
        val store = tempStore()
        store.add(HistoryEntry.fromScreening("first message", "LOW"))
        store.add(HistoryEntry.fromScreening("second message", "MEDIUM"))

        val loaded = store.entries()
        assertEquals(2, loaded.size)
        assertEquals("second message", loaded[0].query)
        assertEquals("MEDIUM", loaded[0].riskLevel)
    }

    @Test
    fun clearRemovesEverything() {
        val store = tempStore()
        store.add(HistoryEntry.fromScreening("anything", "LOW"))
        store.clear()
        assertTrue(store.entries().isEmpty())
    }

    @Test
    fun capsAtMaxEntries() {
        val store = FileHistoryStore(
            File(java.nio.file.Files.createTempDirectory("verifeed-history-cap").toFile(), "history"),
            maxEntries = 3,
        )
        for (i in 1 until 6) {
            store.add(HistoryEntry.fromScreening("message #$i", "LOW"))
        }
        assertEquals(3, store.entries().size)
        assertEquals("message #5", store.entries()[0].query)
    }

    @Test
    fun toleratesCorruptJson() {
        val dir = File(java.nio.file.Files.createTempDirectory("verifeed-history-corrupt").toFile(), "history")
        dir.mkdirs()
        File(dir, "history.json").writeText("{not-valid-json!!")

        val store = FileHistoryStore(dir)
        assertTrue(store.entries().isEmpty())
    }
}