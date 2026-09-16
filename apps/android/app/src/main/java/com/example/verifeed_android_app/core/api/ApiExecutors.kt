package com.example.verifeed_android_app.core.api

import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

/**
 * Shared background executor for network calls so the UI thread is never blocked.
 * androidx.compose state updates from these threads are applied on the next frame.
 */
object ApiExecutors {

    private val pool: ExecutorService = Executors.newFixedThreadPool(2)

    fun execute(task: Runnable) {
        pool.execute(task)
    }

    /** Test helper: drains and stops the pool (idempotent). */
    fun shutdown() {
        pool.shutdown()
        pool.awaitTermination(2, TimeUnit.SECONDS)
    }
}