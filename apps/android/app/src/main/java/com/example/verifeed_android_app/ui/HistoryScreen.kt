@file:OptIn(ExperimentalMaterial3Api::class)

package com.example.verifeed_android_app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
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
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.verifeed_android_app.core.history.HistoryEntry
import com.example.verifeed_android_app.core.history.HistoryStore
import com.example.verifeed_android_app.core.model.RiskLevel
import com.example.verifeed_android_app.core.util.previewText
import com.example.verifeed_android_app.ui.theme.BackgroundDark
import com.example.verifeed_android_app.ui.theme.BorderDark
import com.example.verifeed_android_app.ui.theme.CardDark
import com.example.verifeed_android_app.ui.theme.PrimaryEmerald
import com.example.verifeed_android_app.ui.theme.TextPrimary
import com.example.verifeed_android_app.ui.theme.TextSecondary
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

private val HistoryDateFormatter: DateTimeFormatter = DateTimeFormatter.ofPattern("d MMM yyyy, HH:mm")

/**
 * Sleek Dark HistoryScreen (E7): reverse-chronological list of past verifications
 * stored in the local thread-safe JSON store.
 */
@Composable
fun HistoryScreen(
    padding: PaddingValues,
    historyStore: HistoryStore,
) {
    val entries = remember { mutableStateOf(historyStore.entries()) }

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
                "Investigation History",
                fontWeight = FontWeight.Bold,
                fontSize = 26.sp,
                color = TextPrimary,
            )
        }
        Text(
            "Local history stored securely on this device.",
            fontSize = 14.sp,
            color = TextSecondary,
            modifier = Modifier.padding(top = 4.dp),
        )

        Spacer(Modifier.height(16.dp))

        if (entries.value.isEmpty()) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderDark, RoundedCornerShape(16.dp)),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
            ) {
                Column(
                    modifier = Modifier.padding(24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        "🔍 No investigation history yet",
                        fontWeight = FontWeight.Bold,
                        fontSize = 16.sp,
                        color = TextPrimary
                    )
                    Spacer(Modifier.height(6.dp))
                    Text(
                        "Use the Verify tab to screen messages, URLs, or screenshots.",
                        fontSize = 13.sp,
                        color = TextSecondary
                    )
                }
            }
        } else {
            entries.value.forEach { entry ->
                HistoryEntryCard(
                    entry,
                    modifier = Modifier.padding(bottom = 12.dp),
                )
            }
        }
    }
}

@Composable
private fun HistoryEntryCard(
    entry: HistoryEntry,
    modifier: Modifier = Modifier,
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .border(1.dp, BorderDark, RoundedCornerShape(16.dp)),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = CardDark),
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                RiskBadge(
                    if (entry.riskLevel != null) {
                        RiskLevel.fromApiString(entry.riskLevel)
                    } else {
                        RiskLevel.UNKNOWN
                    },
                )
                Text(
                    formatTimestamp(entry.createdAtEpochMillis),
                    fontSize = 12.sp,
                    color = TextSecondary,
                )
            }

            Spacer(Modifier.height(10.dp))

            Text(
                previewText(entry.query, 120),
                fontSize = 15.sp,
                fontWeight = FontWeight.SemiBold,
                color = TextPrimary,
            )

            entry.summary?.let { summary ->
                Spacer(Modifier.height(4.dp))
                Text(
                    previewText(summary, 120),
                    fontSize = 13.sp,
                    color = TextSecondary,
                )
            }
        }
    }
}

private fun formatTimestamp(epochMillis: Long): String =
    HistoryDateFormatter.format(
        Instant.ofEpochMilli(epochMillis).atZone(ZoneId.systemDefault()),
    )