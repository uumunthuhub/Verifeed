@file:OptIn(ExperimentalMaterial3Api::class)

package com.example.verifeed_android_app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Info
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.Badge
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.verifeed_android_app.core.model.RiskLevel
import com.example.verifeed_android_app.core.model.ScreeningResult
import com.example.verifeed_android_app.core.util.previewText
import com.example.verifeed_android_app.ui.theme.BorderDark
import com.example.verifeed_android_app.ui.theme.CardDark
import com.example.verifeed_android_app.ui.theme.PrimaryEmerald
import com.example.verifeed_android_app.ui.theme.RiskHighColor
import com.example.verifeed_android_app.ui.theme.RiskLowColor
import com.example.verifeed_android_app.ui.theme.RiskMediumColor
import com.example.verifeed_android_app.ui.theme.RiskUnknownColor
import com.example.verifeed_android_app.ui.theme.SurfaceInnerDark
import com.example.verifeed_android_app.ui.theme.TextPrimary
import com.example.verifeed_android_app.ui.theme.TextSecondary

/**
 * Stage 1 result card: sleek dark theme card with vibrant risk badges,
 * structured signal pills, and clear recommended actions.
 */
@Composable
fun ScreeningResultCard(
    result: ScreeningResult,
    modifier: Modifier = Modifier,
) {
    val borderColor = when (result.riskLevel) {
        RiskLevel.HIGH -> RiskHighColor.copy(alpha = 0.6f)
        RiskLevel.MEDIUM -> RiskMediumColor.copy(alpha = 0.6f)
        RiskLevel.LOW -> RiskLowColor.copy(alpha = 0.6f)
        else -> BorderDark
    }

    Card(
        modifier = modifier
            .fillMaxWidth()
            .border(1.dp, borderColor, RoundedCornerShape(20.dp)),
        shape = RoundedCornerShape(20.dp),
        colors = CardDefaults.cardColors(containerColor = CardDark),
    ) {
        Column(modifier = Modifier.padding(20.dp)) {
            // Header Row: Risk Badge + Source Indicator
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                RiskBadge(result.riskLevel)
                
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(12.dp))
                        .background(SurfaceInnerDark)
                        .border(1.dp, BorderDark, RoundedCornerShape(12.dp))
                        .padding(horizontal = 10.dp, vertical = 4.dp)
                ) {
                    Text(
                        if (result.source == ScreeningResult.Stage1Source.LOCAL) "⚡ On-Device Fast Scan" else "🛡️ VeriFeed Threat API",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                        color = TextSecondary,
                    )
                }
            }

            // Recommended Action Banner
            if (result.recommendedAction.isNotEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(top = 16.dp)
                        .clip(RoundedCornerShape(14.dp))
                        .background(
                            when (result.riskLevel) {
                                RiskLevel.HIGH -> RiskHighColor.copy(alpha = 0.15f)
                                RiskLevel.MEDIUM -> RiskMediumColor.copy(alpha = 0.15f)
                                else -> PrimaryEmerald.copy(alpha = 0.15f)
                            }
                        )
                        .border(
                            1.dp,
                            when (result.riskLevel) {
                                RiskLevel.HIGH -> RiskHighColor.copy(alpha = 0.3f)
                                RiskLevel.MEDIUM -> RiskMediumColor.copy(alpha = 0.3f)
                                else -> PrimaryEmerald.copy(alpha = 0.3f)
                            },
                            RoundedCornerShape(14.dp)
                        )
                        .padding(14.dp)
                ) {
                    Row(verticalAlignment = Alignment.Top) {
                        Icon(
                            imageVector = when (result.riskLevel) {
                                RiskLevel.HIGH -> Icons.Default.Warning
                                RiskLevel.MEDIUM -> Icons.Default.Info
                                else -> Icons.Default.Check
                            },
                            contentDescription = null,
                            tint = riskColor(result.riskLevel),
                            modifier = Modifier
                                .size(20.dp)
                                .padding(top = 2.dp)
                        )
                        Spacer(Modifier.width(10.dp))
                        Text(
                            result.recommendedAction,
                            fontSize = 14.sp,
                            fontWeight = FontWeight.Medium,
                            color = TextPrimary,
                        )
                    }
                }
            }

            // Detected Signals Section
            if (result.signals.isNotEmpty()) {
                Text(
                    "Detected Signals (${result.signals.size})",
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    color = TextPrimary,
                    modifier = Modifier.padding(top = 18.dp),
                )
                Column(
                    modifier = Modifier.padding(top = 10.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    result.signals.forEach { signal ->
                        Box(
                            modifier = Modifier
                                .fillMaxWidth()
                                .clip(RoundedCornerShape(12.dp))
                                .background(SurfaceInnerDark)
                                .border(1.dp, BorderDark, RoundedCornerShape(12.dp))
                                .padding(12.dp)
                        ) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Box(
                                    modifier = Modifier
                                        .size(10.dp)
                                        .clip(CircleShape)
                                        .background(severityColor(signal.severity))
                                )
                                Spacer(Modifier.width(10.dp))
                                Column {
                                    Text(
                                        signal.description,
                                        fontSize = 13.sp,
                                        fontWeight = FontWeight.Medium,
                                        color = TextPrimary,
                                    )
                                    if (!signal.matchedText.isNullOrBlank()) {
                                        Text(
                                            "Matched: \"${signal.matchedText}\"",
                                            fontSize = 12.sp,
                                            color = TextSecondary,
                                            modifier = Modifier.padding(top = 2.dp)
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Screened URLs List
            if (result.screenedUrls.isNotEmpty()) {
                Text(
                    "Screened URLs",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = TextPrimary,
                    modifier = Modifier.padding(top = 16.dp),
                )
                result.screenedUrls.forEach { url ->
                    Text(
                        "🔗 ${previewText(url, 48)}",
                        fontSize = 13.sp,
                        color = PrimaryEmerald,
                        modifier = Modifier.padding(top = 4.dp),
                    )
                }
            }

            // Institution Mentions
            if (result.detectedInstitutions.isNotEmpty()) {
                Text(
                    "Mentions Institution: ${result.detectedInstitutions.joinToString(", ")}",
                    fontSize = 13.sp,
                    color = TextSecondary,
                    modifier = Modifier.padding(top = 12.dp),
                )
            }
        }
    }
}

/** Colored pill showing the Stage 1 risk level. */
@Composable
fun RiskBadge(risk: RiskLevel) {
    val bgColor = riskColor(risk)
    Box(
        modifier = Modifier
            .clip(RoundedCornerShape(20.dp))
            .background(bgColor.copy(alpha = 0.2f))
            .border(1.dp, bgColor, RoundedCornerShape(20.dp))
            .padding(horizontal = 14.dp, vertical = 6.dp)
    ) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Box(
                modifier = Modifier
                    .size(8.dp)
                    .clip(CircleShape)
                    .background(bgColor)
            )
            Spacer(Modifier.width(6.dp))
            Text(
                if (risk == RiskLevel.UNKNOWN) "UNCHECKED" else "${risk.name} RISK",
                color = bgColor,
                fontWeight = FontWeight.Bold,
                fontSize = 12.sp,
            )
        }
    }
}

/** Risk level → theme color. */
fun riskColor(risk: RiskLevel): Color =
    when (risk) {
        RiskLevel.LOW -> RiskLowColor
        RiskLevel.MEDIUM -> RiskMediumColor
        RiskLevel.HIGH -> RiskHighColor
        else -> RiskUnknownColor
    }

private fun severityColor(severity: String?): Color =
    when (severity?.lowercase()) {
        "high" -> RiskHighColor
        "medium" -> RiskMediumColor
        "low" -> RiskLowColor
        else -> TextSecondary
    }