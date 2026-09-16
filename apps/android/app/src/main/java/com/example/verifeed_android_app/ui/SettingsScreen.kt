@file:OptIn(ExperimentalMaterial3Api::class)

package com.example.verifeed_android_app.ui

import android.content.Intent
import android.provider.Settings
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.ui.platform.LocalContext
import androidx.core.app.NotificationManagerCompat
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
import androidx.compose.material.icons.filled.Delete
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.Icon
import androidx.compose.material3.Switch
import androidx.compose.material3.SwitchDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.verifeed_android_app.core.api.ApiConfig
import com.example.verifeed_android_app.core.history.HistoryStore
import com.example.verifeed_android_app.core.settings.AppSettings
import com.example.verifeed_android_app.core.settings.AppSettingsStore
import com.example.verifeed_android_app.ui.theme.BackgroundDark
import com.example.verifeed_android_app.ui.theme.BorderDark
import com.example.verifeed_android_app.ui.theme.CardDark
import com.example.verifeed_android_app.ui.theme.PrimaryEmerald
import com.example.verifeed_android_app.ui.theme.SurfaceInnerDark
import com.example.verifeed_android_app.ui.theme.TextPrimary
import com.example.verifeed_android_app.ui.theme.TextSecondary
import com.example.verifeed_android_app.ui.theme.VerdictRed

/**
 * Privacy & permission controls (E8).
 * Dark theme baseline with emerald primary toggles and clear disclosures.
 */
@Composable
fun SettingsScreen(
    padding: PaddingValues,
    historyStore: HistoryStore,
    settingsStore: AppSettingsStore,
    deepVerifyEnabled: MutableState<Boolean>,
    photoPickerEnabled: MutableState<Boolean>,
    remoteStage1Enabled: MutableState<Boolean>,
) {
    val historyCleared = remember { mutableStateOf(false) }
    val context = LocalContext.current
    val isNotificationListenerGranted = remember {
        val enabledListeners = NotificationManagerCompat.getEnabledListenerPackages(context)
        enabledListeners.contains(context.packageName)
    }

    Column(
        Modifier
            .fillMaxSize()
            .background(BackgroundDark)
            .padding(padding)
            .padding(16.dp)
            .verticalScroll(rememberScrollState()),
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .clip(CircleShape)
                    .background(PrimaryEmerald)
            )
            Spacer(Modifier.width(8.dp))
            Text(
                "Privacy & Controls",
                fontWeight = FontWeight.Bold,
                fontSize = 26.sp,
                color = TextPrimary,
            )
        }
        Text(
            "Incremental permissions: VeriFeed never accesses data without user action.",
            fontSize = 13.sp,
            color = TextSecondary,
            modifier = Modifier.padding(top = 4.dp),
        )

        Spacer(Modifier.height(16.dp))

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderDark, RoundedCornerShape(18.dp)),
            shape = RoundedCornerShape(18.dp),
            colors = CardDefaults.cardColors(containerColor = CardDark),
        ) {
            Column(modifier = Modifier.padding(18.dp)) {
                Text(
                    "Granted OS Capabilities",
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    color = TextPrimary,
                )
                Spacer(Modifier.height(10.dp))
                PermissionRow("Internet Access", "Required for Stage 1 threat checks & AI analysis.", granted = true)
                PermissionRow("Photo Picker", "Exercised only when tapping Choose Screenshot.", granted = photoPickerEnabled.value)
                PermissionRow("Share Sheet", "Receives text shared into VeriFeed from other apps.", granted = true)
                PermissionRow(
                    name = "Notification Screener",
                    detail = "Opt-in local protection for SMS, Gmail, WhatsApp & Telegram.",
                    granted = isNotificationListenerGranted,
                    onClick = {
                        try {
                            context.startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
                        } catch (_: Exception) {}
                    }
                )
            }
        }

        Spacer(Modifier.height(16.dp))

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderDark, RoundedCornerShape(18.dp)),
            shape = RoundedCornerShape(18.dp),
            colors = CardDefaults.cardColors(containerColor = CardDark),
        ) {
            Column(modifier = Modifier.padding(18.dp)) {
                Text(
                    "Transmission & Verification Settings",
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    color = TextPrimary,
                )
                Spacer(Modifier.height(10.dp))
                SettingSwitch(
                    label = "Deep VeriFeed AI Analysis",
                    description = "Transmits content to VeriFeed backend for evidence synthesis. Off = local on-device screening only.",
                    value = deepVerifyEnabled,
                ) {
                    persist(settingsStore, deepVerifyEnabled, photoPickerEnabled, remoteStage1Enabled)
                }
                HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp), color = BorderDark)
                SettingSwitch(
                    label = "Remote Stage 1 Screening",
                    description = "Queries Stage 1 threat API for cached institutional scam patterns.",
                    value = remoteStage1Enabled,
                ) {
                    persist(settingsStore, deepVerifyEnabled, photoPickerEnabled, remoteStage1Enabled)
                }
                HorizontalDivider(modifier = Modifier.padding(vertical = 12.dp), color = BorderDark)
                SettingSwitch(
                    label = "Screenshot Upload Action",
                    description = "Enables Photo Picker shortcut on the Verify tab.",
                    value = photoPickerEnabled,
                ) {
                    persist(settingsStore, deepVerifyEnabled, photoPickerEnabled, remoteStage1Enabled)
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        Card(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderDark, RoundedCornerShape(18.dp)),
            shape = RoundedCornerShape(18.dp),
            colors = CardDefaults.cardColors(containerColor = CardDark),
        ) {
            Column(modifier = Modifier.padding(18.dp)) {
                Text(
                    "Local Data Management",
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    color = TextPrimary,
                )
                Spacer(Modifier.height(6.dp))
                Text(
                    "Clears all locally cached investigation records from this device.",
                    fontSize = 12.sp,
                    color = TextSecondary,
                )
                Spacer(Modifier.height(12.dp))
                Button(
                    onClick = {
                        historyStore.clear()
                        historyCleared.value = true
                    },
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(12.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = VerdictRed)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Delete, contentDescription = null, modifier = Modifier.size(16.dp))
                        Spacer(Modifier.width(6.dp))
                        Text("Clear Local History", fontSize = 14.sp, fontWeight = FontWeight.Bold)
                    }
                }
                if (historyCleared.value) {
                    Text(
                        "Local history wiped.",
                        fontSize = 12.sp,
                        color = PrimaryEmerald,
                        modifier = Modifier.padding(top = 8.dp),
                    )
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // API Endpoint Footer Box
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(14.dp))
                .background(SurfaceInnerDark)
                .border(1.dp, BorderDark, RoundedCornerShape(14.dp))
                .padding(14.dp)
        ) {
            Column {
                Text("API Endpoint Target", fontSize = 11.sp, color = TextSecondary)
                Text(ApiConfig.baseUrl, fontSize = 13.sp, fontWeight = FontWeight.Medium, color = PrimaryEmerald)
            }
        }
    }
}

@Composable
private fun PermissionRow(
    name: String,
    detail: String,
    granted: Boolean,
    onClick: (() -> Unit)? = null
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 6.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(name, fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = TextPrimary)
            Text(detail, fontSize = 12.sp, color = TextSecondary)
        }
        Spacer(Modifier.width(8.dp))
        Box(
            modifier = Modifier
                .clip(RoundedCornerShape(8.dp))
                .background(
                    if (granted) PrimaryEmerald.copy(alpha = 0.2f)
                    else if (onClick != null) PrimaryEmerald.copy(alpha = 0.12f)
                    else SurfaceInnerDark
                )
                .border(
                    1.dp,
                    if (granted || onClick != null) PrimaryEmerald else BorderDark,
                    RoundedCornerShape(8.dp)
                )
                .then(if (onClick != null) Modifier.clickable { onClick() } else Modifier)
                .padding(horizontal = 10.dp, vertical = 6.dp)
        ) {
            Text(
                text = if (granted) "Active" else if (onClick != null) "Enable Access" else "Off",
                fontSize = 11.sp,
                fontWeight = FontWeight.Bold,
                color = if (granted || onClick != null) PrimaryEmerald else TextSecondary
            )
        }
    }
}

@Composable
private fun SettingSwitch(
    label: String,
    description: String,
    value: MutableState<Boolean>,
    onChanged: () -> Unit,
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Column(modifier = Modifier.weight(1f)) {
            Text(label, fontWeight = FontWeight.Bold, fontSize = 14.sp, color = TextPrimary)
            Text(description, fontSize = 12.sp, color = TextSecondary, lineHeight = 16.sp)
        }
        Spacer(Modifier.width(8.dp))
        Switch(
            checked = value.value,
            onCheckedChange = { checked ->
                value.value = checked
                onChanged()
            },
            colors = SwitchDefaults.colors(
                checkedThumbColor = BackgroundDark,
                checkedTrackColor = PrimaryEmerald,
                uncheckedThumbColor = TextSecondary,
                uncheckedTrackColor = SurfaceInnerDark
            )
        )
    }
}

private fun persist(
    store: AppSettingsStore,
    deepVerifyEnabled: MutableState<Boolean>,
    photoPickerEnabled: MutableState<Boolean>,
    remoteStage1Enabled: MutableState<Boolean>,
) {
    store.save(
        AppSettings(
            deepVerifyEnabled = deepVerifyEnabled.value,
            photoPickerEnabled = photoPickerEnabled.value,
            remoteStage1Enabled = remoteStage1Enabled.value,
        ),
    )
}