package com.example.verifeed_android_app.ui

import android.net.Uri
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.List
import androidx.compose.material.icons.filled.Search
import androidx.compose.material.icons.filled.Settings
import androidx.compose.material3.Icon
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.MutableState
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.verifeed_android_app.core.history.HistoryStore
import com.example.verifeed_android_app.core.settings.AppSettings
import com.example.verifeed_android_app.core.settings.AppSettingsStore
import com.example.verifeed_android_app.ui.theme.BorderDark
import com.example.verifeed_android_app.ui.theme.PrimaryEmerald
import com.example.verifeed_android_app.ui.theme.PrimaryEmeraldSubtle
import com.example.verifeed_android_app.ui.theme.SurfaceDark
import com.example.verifeed_android_app.ui.theme.TextSecondary

/**
 * Root composable: Scaffold + sleek dark bottom NavigationBar routing between the three
 * primary destinations (Verify / History / Settings).
 */
@Composable
fun VeriFeedApp(
    historyStore: HistoryStore,
    settingsStore: AppSettingsStore,
    openPhotoPicker: () -> Unit,
    shareText: MutableState<String?>,
    pickedMedia: MutableState<Uri?>,
) {
    val selectedTab = remember { mutableStateOf(AppTab.Verify) }
    val loadedPrefs: AppSettings = settingsStore.load()

    val deepVerifyEnabled = remember { mutableStateOf(loadedPrefs.deepVerifyEnabled) }
    val photoPickerEnabled = remember { mutableStateOf(loadedPrefs.photoPickerEnabled) }
    val remoteStage1Enabled = remember { mutableStateOf(loadedPrefs.remoteStage1Enabled) }

    Scaffold(
        modifier = Modifier.fillMaxSize(),
        bottomBar = {
            NavigationBar(
                containerColor = SurfaceDark,
                modifier = Modifier.border(width = 0.5.dp, color = BorderDark),
            ) {
                val itemColors = NavigationBarItemDefaults.colors(
                    selectedIconColor = PrimaryEmerald,
                    selectedTextColor = PrimaryEmerald,
                    indicatorColor = PrimaryEmeraldSubtle,
                    unselectedIconColor = TextSecondary,
                    unselectedTextColor = TextSecondary,
                )

                NavigationBarItem(
                    selected = selectedTab.value == AppTab.Verify,
                    onClick = { selectedTab.value = AppTab.Verify },
                    icon = { Icon(Icons.Default.Search, contentDescription = "Verify") },
                    label = { Text("Verify", fontSize = 12.sp, fontWeight = if (selectedTab.value == AppTab.Verify) FontWeight.Bold else FontWeight.Normal) },
                    colors = itemColors,
                )
                NavigationBarItem(
                    selected = selectedTab.value == AppTab.History,
                    onClick = { selectedTab.value = AppTab.History },
                    icon = { Icon(Icons.Default.List, contentDescription = "History") },
                    label = { Text("History", fontSize = 12.sp, fontWeight = if (selectedTab.value == AppTab.History) FontWeight.Bold else FontWeight.Normal) },
                    colors = itemColors,
                )
                NavigationBarItem(
                    selected = selectedTab.value == AppTab.Settings,
                    onClick = { selectedTab.value = AppTab.Settings },
                    icon = { Icon(Icons.Default.Settings, contentDescription = "Settings") },
                    label = { Text("Settings", fontSize = 12.sp, fontWeight = if (selectedTab.value == AppTab.Settings) FontWeight.Bold else FontWeight.Normal) },
                    colors = itemColors,
                )
            }
        },
    ) { innerPadding ->
        when (selectedTab.value) {
            AppTab.Verify ->
                VerifyScreen(
                    padding = innerPadding,
                    historyStore = historyStore,
                    deepVerifyEnabled = deepVerifyEnabled,
                    photoPickerEnabled = photoPickerEnabled,
                    remoteStage1Enabled = remoteStage1Enabled,
                    openPhotoPicker = openPhotoPicker,
                    shareText = shareText,
                    pickedMedia = pickedMedia,
                )
            AppTab.History -> HistoryScreen(innerPadding, historyStore)
            AppTab.Settings ->
                SettingsScreen(
                    padding = innerPadding,
                    historyStore = historyStore,
                    settingsStore = settingsStore,
                    deepVerifyEnabled = deepVerifyEnabled,
                    photoPickerEnabled = photoPickerEnabled,
                    remoteStage1Enabled = remoteStage1Enabled,
                )
        }
    }
}