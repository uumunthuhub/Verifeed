@file:OptIn(ExperimentalMaterial3Api::class)

package com.example.verifeed_android_app.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.example.verifeed_android_app.core.model.VerificationSummary
import com.example.verifeed_android_app.ui.theme.BorderDark
import com.example.verifeed_android_app.ui.theme.BorderEmerald
import com.example.verifeed_android_app.ui.theme.CardDark
import com.example.verifeed_android_app.ui.theme.PrimaryEmerald
import com.example.verifeed_android_app.ui.theme.SurfaceInnerDark
import com.example.verifeed_android_app.ui.theme.TextPrimary
import com.example.verifeed_android_app.ui.theme.TextSecondary
import com.example.verifeed_android_app.ui.theme.VerdictGreen
import com.example.verifeed_android_app.ui.theme.VerdictRed
import com.example.verifeed_android_app.ui.theme.VerdictAmber

/**
 * Stage 2 result: Sleek evidence-backed agent investigation report.
 * Features dual-verdict card grid, confidence meter, extracted entity chips,
 * ranked evidence sources, and structured methodology explanation.
 */
@Composable
fun VerificationResultScreen(
    result: VerificationSummary,
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(top = 16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Section Header
        Row(
            verticalAlignment = Alignment.CenterVertically,
            modifier = Modifier.padding(horizontal = 4.dp)
        ) {
            Box(
                modifier = Modifier
                    .size(10.dp)
                    .clip(CircleShape)
                    .background(PrimaryEmerald)
            )
            Spacer(Modifier.width(8.dp))
            Text(
                "VeriFeed Agent Investigation Report",
                fontWeight = FontWeight.Bold,
                fontSize = 18.sp,
                color = TextPrimary
            )
        }

        // Dual Verdict Cards Container
        Card(
            modifier = Modifier
                .fillMaxWidth()
                .border(1.dp, BorderEmerald.copy(alpha = 0.4f), RoundedCornerShape(20.dp)),
            shape = RoundedCornerShape(20.dp),
            colors = CardDefaults.cardColors(containerColor = CardDark),
        ) {
            Column(modifier = Modifier.padding(20.dp)) {
                Text(
                    "Dual-Verdict System",
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp,
                    color = TextSecondary
                )

                Spacer(Modifier.height(12.dp))

                // Verdict 1: Claim Factual Verdict
                VerdictItemCard(
                    title = "Factual Claim Verdict",
                    subtitle = "Truthfulness of statement",
                    verdictText = result.claimVerdict ?: result.verdict
                )

                Spacer(Modifier.height(10.dp))

                // Verdict 2: Message Authenticity Verdict
                VerdictItemCard(
                    title = "Message Authenticity Verdict",
                    subtitle = "Legitimacy of communication channel",
                    verdictText = result.messageAuthenticityVerdict ?: "AUTHENTICITY CHECKED"
                )

                // Confidence Bar
                if (result.confidenceScore > 0.0) {
                    val pct = (result.confidenceScore * 100).toInt()
                    Column(modifier = Modifier.padding(top = 16.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween
                        ) {
                            Text("Investigation Confidence", fontSize = 12.sp, color = TextSecondary)
                            Text("$pct%", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = PrimaryEmerald)
                        }
                        Spacer(Modifier.height(6.dp))
                        LinearProgressIndicator(
                            progress = { result.confidenceScore.toFloat() },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(6.dp)
                                .clip(RoundedCornerShape(3.dp)),
                            color = PrimaryEmerald,
                            trackColor = SurfaceInnerDark,
                        )
                    }
                }
            }
        }

        // Executive Summary Card
        if (result.summary.isNotEmpty()) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderDark, RoundedCornerShape(16.dp)),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        "Executive Summary",
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp,
                        color = TextPrimary
                    )
                    Spacer(Modifier.height(8.dp))
                    Text(
                        result.summary,
                        fontSize = 14.sp,
                        color = TextSecondary,
                        lineHeight = 20.sp
                    )
                }
            }
        }

        // Extracted Entities Chips
        if (result.extractedSender != null || result.extractedNumbers.isNotEmpty() ||
            result.extractedUrls.isNotEmpty() || result.extractedInstitutions.isNotEmpty()
        ) {
            Card(
                modifier = Modifier
                    .fillMaxWidth()
                    .border(1.dp, BorderDark, RoundedCornerShape(16.dp)),
                shape = RoundedCornerShape(16.dp),
                colors = CardDefaults.cardColors(containerColor = CardDark),
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text(
                        "Extracted Entities & Metadata",
                        fontWeight = FontWeight.Bold,
                        fontSize = 14.sp,
                        color = TextPrimary
                    )
                    Spacer(Modifier.height(10.dp))

                    if (result.extractedSender != null) {
                        EntityRow("Sender", result.extractedSender)
                    }
                    if (result.extractedNumbers.isNotEmpty()) {
                        EntityRow("Phones / Shortcodes", result.extractedNumbers.joinToString(", "))
                    }
                    if (result.extractedUrls.isNotEmpty()) {
                        EntityRow("Extracted URLs", result.extractedUrls.joinToString(", "))
                    }
                    if (result.extractedInstitutions.isNotEmpty()) {
                        EntityRow("Institutions", result.extractedInstitutions.joinToString(", "))
                    }
                }
            }
        }

        // Evidence Sources Section
        if (result.sources.isNotEmpty()) {
            Column {
                Text(
                    "Retrieved Evidence Sources (${result.sources.size})",
                    fontWeight = FontWeight.Bold,
                    fontSize = 15.sp,
                    color = TextPrimary,
                    modifier = Modifier.padding(bottom = 10.dp)
                )

                result.sources.forEach { source ->
                    Card(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(bottom = 10.dp)
                            .border(1.dp, BorderDark, RoundedCornerShape(14.dp)),
                        shape = RoundedCornerShape(14.dp),
                        colors = CardDefaults.cardColors(containerColor = CardDark),
                    ) {
                        Column(modifier = Modifier.padding(14.dp)) {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Text(
                                    source.outlet.ifEmpty { source.type },
                                    fontWeight = FontWeight.Bold,
                                    fontSize = 12.sp,
                                    color = PrimaryEmerald
                                )
                                Text(
                                    source.type,
                                    fontSize = 11.sp,
                                    color = TextSecondary
                                )
                            }
                            Spacer(Modifier.height(4.dp))
                            Text(
                                source.title,
                                fontWeight = FontWeight.SemiBold,
                                fontSize = 14.sp,
                                color = TextPrimary
                            )
                            source.snippet?.let { snippet ->
                                Spacer(Modifier.height(6.dp))
                                Text(
                                    snippet,
                                    fontSize = 12.sp,
                                    color = TextSecondary,
                                    maxLines = 3
                                )
                            }
                        }
                    }
                }
            }
        }

        // Verification Methodology
        result.methodology?.let { method ->
            if (method.isNotEmpty()) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .border(1.dp, BorderDark, RoundedCornerShape(16.dp)),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(containerColor = SurfaceInnerDark),
                ) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text(
                            "🔬 Verification Methodology",
                            fontWeight = FontWeight.Bold,
                            fontSize = 13.sp,
                            color = PrimaryEmerald
                        )
                        Spacer(Modifier.height(6.dp))
                        Text(
                            method,
                            fontSize = 12.sp,
                            color = TextSecondary,
                            lineHeight = 18.sp
                        )
                    }
                }
            }
        }
    }
}

@Composable
private fun VerdictItemCard(title: String, subtitle: String, verdictText: String) {
    val (vColor, vBg) = when {
        verdictText.contains("FALSE", true) || verdictText.contains("SCAM", true) || verdictText.contains("PHISHING", true) -> Pair(VerdictRed, VerdictRed.copy(alpha = 0.15f))
        verdictText.contains("TRUE", true) || verdictText.contains("AUTHENTIC", true) -> Pair(VerdictGreen, VerdictGreen.copy(alpha = 0.15f))
        else -> Pair(VerdictAmber, VerdictAmber.copy(alpha = 0.15f))
    }

    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(14.dp))
            .background(SurfaceInnerDark)
            .border(1.dp, BorderDark, RoundedCornerShape(14.dp))
            .padding(14.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(title, fontWeight = FontWeight.Bold, fontSize = 13.sp, color = TextPrimary)
                Text(subtitle, fontSize = 11.sp, color = TextSecondary)
            }
            Spacer(Modifier.width(8.dp))
            Box(
                modifier = Modifier
                    .clip(RoundedCornerShape(10.dp))
                    .background(vBg)
                    .border(1.dp, vColor, RoundedCornerShape(10.dp))
                    .padding(horizontal = 12.dp, vertical = 6.dp)
            ) {
                Text(
                    verdictText.uppercase(),
                    color = vColor,
                    fontWeight = FontWeight.Bold,
                    fontSize = 12.sp
                )
            }
        }
    }
}

@Composable
private fun EntityRow(label: String, value: String) {
    Column(modifier = Modifier.padding(vertical = 4.dp)) {
        Text(label, fontSize = 11.sp, color = TextSecondary)
        Text(value, fontSize = 13.sp, fontWeight = FontWeight.Medium, color = PrimaryEmerald)
    }
}