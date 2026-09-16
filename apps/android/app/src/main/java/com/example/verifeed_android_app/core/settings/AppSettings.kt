package com.example.verifeed_android_app.core.settings

/**
 * User privacy/permission preferences (E8).
 *
 * All toggles are OFF by default — permission-minimized. The "deep verification"
 * toggle controls whether content is transmitted to the VeriFeed API at all;
 * local screening always stays on-device.
 */
data class AppSettings(
    val deepVerifyEnabled: Boolean = false,
    val photoPickerEnabled: Boolean = false,
    val remoteStage1Enabled: Boolean = false,
)