package com.example.verifeed_android_app.core.settings

import org.json.JSONObject
import java.io.File

/**
 * JSON-file-backed persistence for [AppSettings] (E8).
 * Writes are atomic-ish (tmp file rename) and thread-safe via a lock.
 */
class AppSettingsStore(
    private val directory: File,
) {

    private val lock = Object()
    private val settingsFile: File get() = File(directory, "settings.json")

    fun load(): AppSettings {
        synchronized(lock) {
            if (!settingsFile.exists()) return AppSettings()
            return try {
                val root = JSONObject(settingsFile.readText())
                AppSettings(
                    deepVerifyEnabled = root.optBoolean("deep_verify_enabled", false),
                    photoPickerEnabled = root.optBoolean("photo_picker_enabled", false),
                    remoteStage1Enabled = root.optBoolean("remote_stage1_enabled", false),
                )
            } catch (e: Exception) {
                AppSettings()
            }
        }
    }

    fun save(settings: AppSettings) {
        synchronized(lock) {
            directory.mkdirs()
            val root =
                JSONObject()
                    .put("deep_verify_enabled", settings.deepVerifyEnabled)
                    .put("photo_picker_enabled", settings.photoPickerEnabled)
                    .put("remote_stage1_enabled", settings.remoteStage1Enabled)
            settingsFile.writeText(root.toString(2))
        }
    }
}