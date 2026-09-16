package com.example.verifeed_android_app

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import com.example.verifeed_android_app.core.history.FileHistoryStore
import com.example.verifeed_android_app.core.settings.AppSettingsStore
import com.example.verifeed_android_app.ui.SplashScreen
import com.example.verifeed_android_app.ui.VeriFeedApp
import com.example.verifeed_android_app.ui.theme.VerifeedandroidappTheme
import java.io.File

/**
 * VeriFeed main activity (Phase E).
 *
 * Wires the Compose UI to the OS integrations:
 * - Animated Splash Screen startup transition
 * - SEND share-sheet intent → "Share → VeriFeed" from any app (E6)
 * - Photo Picker → screenshot verification (E4)
 * - Local file-backed history + settings stores (E7/E8)
 */
class MainActivity : ComponentActivity() {

    private companion object {
        const val REQUEST_PICK_MEDIA: Int = 0x1001

        const val ACTION_SEND: String = "android.intent.action.SEND"
        const val EXTRA_TITLE: String = "android.intent.extra.TITLE"
        const val EXTRA_TEXT: String = "android.intent.extra.TEXT"

        /** API 33+ returns android.app.Activity.RESULT_OK = -1 from the media picker. */
        const val RESULT_OK: Int = -1
    }

    private val shareTextState: MutableState<String?> = mutableStateOf(null)
    private val pickedMediaState: MutableState<Uri?> = mutableStateOf(null)

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val dataDir = File(filesDir, "verifeed_history")
        val historyStore = FileHistoryStore(dataDir)
        val settingsStore = AppSettingsStore(dataDir)

        setContent {
            VerifeedandroidappTheme {
                val showSplash = remember { mutableStateOf(true) }

                if (showSplash.value) {
                    SplashScreen(
                        onSplashComplete = { showSplash.value = false }
                    )
                } else {
                    VeriFeedApp(
                        historyStore = historyStore,
                        settingsStore = settingsStore,
                        openPhotoPicker = { launchPhotoPicker() },
                        shareText = shareTextState,
                        pickedMedia = pickedMediaState,
                    )
                }
            }
        }
    }

    // ------------------------------------------------------------------
    // E4 — Screenshot capture via the OS Photo Picker
    // ------------------------------------------------------------------

    private fun launchPhotoPicker() {
        val contract = ActivityResultContracts.PickVisualMedia()
        val request = PickVisualMediaRequest(mediaType = ActivityResultContracts.PickVisualMedia.ImageOnly)
        startActivityForResult(contract.createIntent(this, request), REQUEST_PICK_MEDIA)
    }

    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode == REQUEST_PICK_MEDIA && resultCode == RESULT_OK && data != null) {
            (data.data as? Uri)?.let { uri ->
                pickedMediaState.value = uri
            }
        }
    }

    // ------------------------------------------------------------------
    // E6 — Share sheet receiver ("Share → VeriFeed" from any app)
    // ------------------------------------------------------------------

    override fun onNewIntent(@Suppress("InvalidNullabilityOverride") intent: Intent) {
        super.onNewIntent(intent)
        if (intent.action == ACTION_SEND) {
            val text = intent.getStringExtra(EXTRA_TEXT)
            val title = intent.getStringExtra(EXTRA_TITLE)
            val payload = text ?: title
            if (payload != null) {
                shareTextState.value = payload
            }
        }
    }
}