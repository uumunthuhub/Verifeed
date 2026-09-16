@file:OptIn(ExperimentalMaterial3Api::class)

package com.example.verifeed_android_app.ui

import android.net.Uri
import android.os.Handler
import android.os.Looper
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Clear
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.res.painterResource
import com.example.verifeed_android_app.R
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.verifeed_android_app.core.api.ApiExecutors
import com.example.verifeed_android_app.core.api.VeriFeedApiClient
import com.example.verifeed_android_app.core.history.HistoryEntry
import com.example.verifeed_android_app.core.history.HistoryStore
import com.example.verifeed_android_app.core.model.ScreeningResult
import com.example.verifeed_android_app.core.model.VerificationSummary
import com.example.verifeed_android_app.core.screening.LocalScreeningEngine
import com.example.verifeed_android_app.core.util.previewText
import com.example.verifeed_android_app.ui.theme.BackgroundDark
import com.example.verifeed_android_app.ui.theme.BorderDark
import com.example.verifeed_android_app.ui.theme.BorderEmerald
import com.example.verifeed_android_app.ui.theme.BorderEmeraldSubtle
import com.example.verifeed_android_app.ui.theme.CardDark
import com.example.verifeed_android_app.ui.theme.PrimaryEmerald
import com.example.verifeed_android_app.ui.theme.SurfaceInnerDark
import com.example.verifeed_android_app.ui.theme.TextPrimary
import com.example.verifeed_android_app.ui.theme.TextSecondary
import com.example.verifeed_android_app.ui.theme.VerdictGreen
import com.example.verifeed_android_app.ui.theme.VerdictRed
import java.io.File
import java.util.Base64

private val mainHandler = Handler(Looper.getMainLooper())

/**
 * Home UI (VerifyScreen): Sleek Agent-Like Container matching the web app.
 * Integrated chat widget input card with attached screenshot badge on top of input,
 * in-container attachment pill button, quick sample prompt chips, vibrant green action buttons,
 * and structured Stage 1 & Stage 2 outputs.
 */
@Composable
fun VerifyScreen(
    padding: PaddingValues,
    historyStore: HistoryStore,
    deepVerifyEnabled: MutableState<Boolean>,
    photoPickerEnabled: MutableState<Boolean>,
    remoteStage1Enabled: MutableState<Boolean>,
    openPhotoPicker: () -> Unit,
    shareText: MutableState<String?>,
    pickedMedia: MutableState<Uri?>,
) {
    val input = remember { mutableStateOf("") }
    val apiClient = remember { VeriFeedApiClient() }
    val localEngine = remember { LocalScreeningEngine() }

    val screening = remember { mutableStateOf<ScreeningResult?>(null) }
    val verification = remember { mutableStateOf<VerificationSummary?>(null) }
    val busy = remember { mutableStateOf(false) }
    val errorMessage = remember { mutableStateOf<String?>(null) }
    val reportConfirmation = remember { mutableStateOf<String?>(null) }

    // Consume share-sheet payload
    shareText.value?.let { shared ->
        if (shared.isNotBlank()) {
            input.value = shared
            shareText.value = null
        }
    }

    val sampleClaims = listOf(
        "Standard Bank WhatsApp collateral free loans",
        "Airtel Money calling for secret PIN",
        "Free iPhone lottery gift card link",
        "WHO declares global health emergency"
    )

    Column(
        Modifier
            .fillMaxSize()
            .background(BackgroundDark)
            .padding(padding)
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
    ) {
        // Top Branding Header Bar — Web App "VF" Logo Mark + "VeriFeed"
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(bottom = 12.dp)
        ) {
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier
                    .size(34.dp)
                    .clip(RoundedCornerShape(9.dp))
                    .background(
                        Brush.linearGradient(
                            colors = listOf(PrimaryEmerald, Color(0xFF059669))
                        )
                    )
            ) {
                Text(
                    text = "VF",
                    color = Color.White,
                    fontWeight = FontWeight.Black,
                    fontSize = 15.sp,
                    letterSpacing = (-0.5).sp
                )
            }
            Spacer(Modifier.width(10.dp))
            Text(
                "VeriFeed",
                fontWeight = FontWeight.Bold,
                fontSize = 24.sp,
                color = TextPrimary,
                letterSpacing = 0.5.sp
            )
        }

        Text(
            "Verify Anything",
            fontWeight = FontWeight.Bold,
            fontSize = 30.sp,
            color = TextPrimary,
        )
        Text(
            "Detect misinformation, SMS phishing, and fake claims with evidence.",
            fontSize = 14.sp,
            color = TextSecondary,
            modifier = Modifier.padding(top = 2.dp),
        )

        Spacer(Modifier.height(16.dp))

        // --- Sleek AI Agent Chat Container ---
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderEmeraldSubtle, RoundedCornerShape(24.dp)),
            shape = RoundedCornerShape(24.dp),
            colors = CardDefaults.cardColors(containerColor = CardDark),
        ) {
            Column(modifier = Modifier.padding(18.dp)) {
                
                Text(
                    "Ask VeriFeed Agent",
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    color = TextPrimary
                )

                Spacer(Modifier.height(12.dp))

                // --- Integrated Chat Widget Input Card ---
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(18.dp))
                        .background(SurfaceInnerDark)
                        .border(1.dp, BorderDark, RoundedCornerShape(18.dp))
                        .padding(14.dp)
                ) {
                    Column {
                        // Attached Media Thumbnail/Badge (On top of input field inside card)
                        pickedMedia.value?.let { uri ->
                            Box(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(bottom = 10.dp)
                                    .clip(RoundedCornerShape(12.dp))
                                    .background(CardDark)
                                    .border(1.dp, PrimaryEmerald, RoundedCornerShape(12.dp))
                                    .padding(horizontal = 12.dp, vertical = 8.dp)
                            ) {
                                Row(
                                    modifier = Modifier.fillMaxWidth(),
                                    horizontalArrangement = Arrangement.SpaceBetween,
                                    verticalAlignment = Alignment.CenterVertically
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text("🖼️", fontSize = 14.sp)
                                        Spacer(Modifier.width(8.dp))
                                        Column {
                                            Text(
                                                "Attached Screenshot",
                                                fontSize = 12.sp,
                                                fontWeight = FontWeight.Bold,
                                                color = PrimaryEmerald
                                            )
                                            Text(
                                                previewText(uri.path ?: "screenshot.png", 28),
                                                fontSize = 11.sp,
                                                color = TextSecondary
                                            )
                                        }
                                    }
                                    IconButton(
                                        onClick = { pickedMedia.value = null },
                                        modifier = Modifier.size(24.dp)
                                    ) {
                                        Icon(Icons.Default.Clear, contentDescription = "Remove", tint = TextSecondary)
                                    }
                                }
                            }
                        }

                        // Text Field
                        OutlinedTextField(
                            value = input.value,
                            onValueChange = { input.value = it },
                            placeholder = {
                                Text(
                                    "Paste suspicious SMS, WhatsApp message, news claim, or URL...",
                                    fontSize = 14.sp,
                                    color = TextSecondary
                                )
                            },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(110.dp),
                            shape = RoundedCornerShape(12.dp),
                            colors = OutlinedTextFieldDefaults.colors(
                                focusedContainerColor = SurfaceInnerDark,
                                unfocusedContainerColor = SurfaceInnerDark,
                                focusedBorderColor = Color.Transparent,
                                unfocusedBorderColor = Color.Transparent,
                                focusedTextColor = TextPrimary,
                                unfocusedTextColor = TextPrimary,
                                cursorColor = PrimaryEmerald,
                            )
                        )

                        Spacer(Modifier.height(8.dp))

                        // Bottom Toolbar inside the input widget card
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            // Screenshot / Attachment Button inside widget
                            if (photoPickerEnabled.value) {
                                Box(
                                    modifier = Modifier
                                        .clip(RoundedCornerShape(12.dp))
                                        .background(PrimaryEmerald.copy(alpha = 0.15f))
                                        .border(1.dp, PrimaryEmerald.copy(alpha = 0.5f), RoundedCornerShape(12.dp))
                                        .clickable { openPhotoPicker() }
                                        .padding(horizontal = 12.dp, vertical = 6.dp)
                                ) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Icon(
                                            Icons.Default.Add,
                                            contentDescription = "Attach Screenshot",
                                            tint = PrimaryEmerald,
                                            modifier = Modifier.size(16.dp)
                                        )
                                        Spacer(Modifier.width(6.dp))
                                        Text(
                                            "📷 Screenshot",
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = PrimaryEmerald
                                        )
                                    }
                                }
                            } else {
                                Spacer(Modifier.width(1.dp))
                            }

                            if (input.value.isNotEmpty()) {
                                IconButton(
                                    onClick = { input.value = "" },
                                    modifier = Modifier.size(28.dp)
                                ) {
                                    Icon(Icons.Default.Clear, contentDescription = "Clear", tint = TextSecondary)
                                }
                            }
                        }
                    }
                }

                // Quick Prompt Pills Horizontal Scroll
                Spacer(Modifier.height(14.dp))
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState()),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    sampleClaims.forEach { claim ->
                        Box(
                            modifier = Modifier
                                .clip(RoundedCornerShape(16.dp))
                                .background(SurfaceInnerDark)
                                .border(1.dp, BorderDark, RoundedCornerShape(16.dp))
                                .clickable { input.value = claim }
                                .padding(horizontal = 12.dp, vertical = 6.dp)
                        ) {
                            Text(
                                "💡 $claim",
                                fontSize = 12.sp,
                                color = TextSecondary
                            )
                        }
                    }
                }

                Spacer(Modifier.height(16.dp))

                // Primary Emerald Action Button (Stage 2 Deep Verify)
                Button(
                    onClick = {
                        runDeepVerification(
                            input, apiClient, localEngine, deepVerifyEnabled,
                            screening, verification, busy, errorMessage, historyStore, pickedMedia
                        )
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(52.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = PrimaryEmerald,
                        contentColor = BackgroundDark
                    ),
                    enabled = !busy.value
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Search, contentDescription = null, modifier = Modifier.size(20.dp))
                        Spacer(Modifier.width(8.dp))
                        Text(
                            "⚡ Analyze with VeriFeed AI",
                            fontSize = 16.sp,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }

                Spacer(Modifier.height(8.dp))

                // Secondary Outlined Action Button (Stage 1 On-Device Scan)
                OutlinedButton(
                    onClick = {
                        runScreening(
                            input, apiClient, localEngine, remoteStage1Enabled,
                            screening, verification, busy, errorMessage, historyStore, pickedMedia
                        )
                    },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(44.dp),
                    shape = RoundedCornerShape(14.dp),
                    colors = ButtonDefaults.outlinedButtonColors(contentColor = PrimaryEmerald),
                    border = androidx.compose.foundation.BorderStroke(1.dp, PrimaryEmerald.copy(alpha = 0.5f))
                ) {
                    Text(
                        "🔍 Fast On-Device Scan",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.SemiBold
                    )
                }
            }
        }

        // Busy Indicator
        if (busy.value) {
            Spacer(Modifier.height(16.dp))
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .background(CardDark)
                    .padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        "🤖 VeriFeed Agent is investigating evidence…",
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium,
                        color = PrimaryEmerald
                    )
                }
            }
        }

        // Error & Confirmation Messages
        errorMessage.value?.let { message ->
            Spacer(Modifier.height(12.dp))
            Text(message, fontSize = 14.sp, color = VerdictRed)
        }
        reportConfirmation.value?.let { message ->
            Spacer(Modifier.height(12.dp))
            Text(message, fontSize = 14.sp, color = VerdictGreen)
        }

        // --- Render Stage 1 Screening Output ---
        screening.value?.let { result ->
            Spacer(Modifier.height(16.dp))
            ScreeningResultCard(result)
        }

        // --- Render Stage 2 Deep Verification Output ---
        verification.value?.let { result ->
            Spacer(Modifier.height(16.dp))
            VerificationResultScreen(result)

            Spacer(Modifier.height(16.dp))
            Button(
                onClick = { reportScam(input, apiClient, reportConfirmation, errorMessage) },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(48.dp),
                shape = RoundedCornerShape(14.dp),
                colors = ButtonDefaults.buttonColors(containerColor = VerdictRed)
            ) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Default.Warning, contentDescription = "Report", modifier = Modifier.size(18.dp))
                    Spacer(Modifier.width(8.dp))
                    Text("🚩 Report as Scam Campaign", fontSize = 15.sp, fontWeight = FontWeight.Bold)
                }
            }
        }
    }
}

/** Stage 1: instant on-device analysis (+ optional remote screening). */
private fun runScreening(
    input: MutableState<String>,
    apiClient: VeriFeedApiClient,
    localEngine: LocalScreeningEngine,
    remoteStage1Enabled: MutableState<Boolean>,
    screening: MutableState<ScreeningResult?>,
    verification: MutableState<VerificationSummary?>,
    busy: MutableState<Boolean>,
    errorMessage: MutableState<String?>,
    historyStore: HistoryStore,
    pickedMedia: MutableState<Uri?>,
) {
    val content = input.value
    busy.value = true
    errorMessage.value = null
    ApiExecutors.execute {
        try {
            val local = localEngine.screen(content)
            val result =
                if (remoteStage1Enabled.value && content.isNotBlank()) {
                    try {
                        apiClient.screen(content)
                    } catch (e: Exception) {
                        local // graceful offline fallback
                    }
                } else {
                    local
                }
            mainHandler.post {
                screening.value = result
                verification.value = null
                busy.value = false
            }
        } catch (e: Exception) {
            mainHandler.post {
                errorMessage.value = "Screening failed: ${e.localizedMessage ?: "Check connection."}"
                busy.value = false
            }
        }
    }
}

/** Stage 2: full deep investigation. */
private fun runDeepVerification(
    input: MutableState<String>,
    apiClient: VeriFeedApiClient,
    localEngine: LocalScreeningEngine,
    deepVerifyEnabled: MutableState<Boolean>,
    screening: MutableState<ScreeningResult?>,
    verification: MutableState<VerificationSummary?>,
    busy: MutableState<Boolean>,
    errorMessage: MutableState<String?>,
    historyStore: HistoryStore,
    pickedMedia: MutableState<Uri?>,
) {
    val content = input.value
    val mediaUri = pickedMedia.value
    if (content.isBlank() && mediaUri == null) {
        errorMessage.value = "Please enter text or choose a screenshot to verify."
        return
    }

    busy.value = true
    errorMessage.value = null

    ApiExecutors.execute {
        try {
            val priorScreening = localEngine.screen(content)
            val base64Image: String? = mediaUri?.let { uri ->
                try {
                    val file = File(uri.path ?: "")
                    if (file.exists()) {
                        Base64.getEncoder().encodeToString(file.readBytes())
                    } else null
                } catch (e: Exception) {
                    null
                }
            }

            val summary = if (deepVerifyEnabled.value) {
                try {
                    apiClient.verify(query = content, priorScreening = priorScreening, imageDataBase64 = base64Image)
                } catch (e: Exception) {
                    // Fallback to Stage 1 offline summary if network is unreachable
                    VerificationSummary(
                        id = (System.currentTimeMillis() % 100000).toInt(),
                        query = content,
                        verdict = priorScreening.riskLevel.name,
                        summary = priorScreening.recommendedAction,
                        claimVerdict = "UNVERIFIED (OFFLINE)",
                        messageAuthenticityVerdict = priorScreening.riskLevel.name + " RISK",
                        confidenceScore = 0.5,
                        sources = emptyList(),
                        extractedSender = null,
                        extractedNumbers = emptyList(),
                        extractedUrls = priorScreening.screenedUrls,
                        extractedInstitutions = priorScreening.detectedInstitutions,
                        recommendedActions = listOf(priorScreening.recommendedAction),
                        methodology = "On-device local screening fallback (network unreachable)."
                    )
                }
            } else {
                VerificationSummary(
                    id = (System.currentTimeMillis() % 100000).toInt(),
                    query = content,
                    verdict = priorScreening.riskLevel.name,
                    summary = priorScreening.recommendedAction,
                    claimVerdict = "LOCAL SCREENING",
                    messageAuthenticityVerdict = priorScreening.riskLevel.name + " RISK",
                    confidenceScore = 0.6,
                    sources = emptyList(),
                    extractedSender = null,
                    extractedNumbers = emptyList(),
                    extractedUrls = priorScreening.screenedUrls,
                    extractedInstitutions = priorScreening.detectedInstitutions,
                    recommendedActions = listOf(priorScreening.recommendedAction),
                    methodology = "Local screening only (Deep verification disabled in settings)."
                )
            }

            // Save to history
            val entry = HistoryEntry.fromVerification(
                query = content.ifBlank { "Screenshot verification" },
                verification = summary
            )
            historyStore.add(entry)

            mainHandler.post {
                screening.value = priorScreening
                verification.value = summary
                busy.value = false
            }
        } catch (e: Exception) {
            mainHandler.post {
                errorMessage.value = "Verification failed: ${e.localizedMessage ?: "Unknown error"}"
                busy.value = false
            }
        }
    }
}

private fun reportScam(
    input: MutableState<String>,
    apiClient: VeriFeedApiClient,
    reportConfirmation: MutableState<String?>,
    errorMessage: MutableState<String?>,
) {
    val text = input.value.trim()
    if (text.isBlank()) return

    ApiExecutors.execute {
        try {
            val ok = apiClient.reportScam(text)
            mainHandler.post {
                if (ok) {
                    reportConfirmation.value = "Thank you! Scam report submitted to VeriFeed Intelligence."
                } else {
                    errorMessage.value = "Could not submit report."
                }
            }
        } catch (e: Exception) {
            mainHandler.post {
                errorMessage.value = "Report error: ${e.localizedMessage}"
            }
        }
    }
}