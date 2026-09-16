package com.example.verifeed_android_app

import androidx.compose.ui.test.hasText
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * Phase E smoke test (Gate E): the app must launch and render the Verify tab
 * on a real device/emulator. Run with:
 *
 *   cd apps/android && ./gradlew connectedDebugAndroidTest
 */
@RunWith(AndroidJUnit4::class)
class MainActivitySmokeTest {

    @get:Rule
    val composeTest = createAndroidComposeRule<MainActivity>()

    @Test
    fun launchesAndRendersVerifyScreen() {
        composeTest.waitForIdle()
        // The root Scaffold must be composed and the title visible.
        composeTest.onNode(hasText("VeriFeed", substring = true)).assertExists()
    }
}