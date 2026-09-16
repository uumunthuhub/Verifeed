package com.example.verifeed_android_app.ui

import androidx.compose.animation.core.Animatable
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import com.example.verifeed_android_app.R
import com.example.verifeed_android_app.ui.theme.BackgroundDark
import com.example.verifeed_android_app.ui.theme.PrimaryEmerald
import com.example.verifeed_android_app.ui.theme.PrimaryEmeraldLight
import com.example.verifeed_android_app.ui.theme.TextPrimary
import com.example.verifeed_android_app.ui.theme.TextSecondary
import kotlinx.coroutines.delay

/**
 * Animated Splash Screen:
 * - Smooth logo scale-in & alpha fade animation
 * - Glowing emerald pulse ring effect
 * - Brand typography & capability pill badge
 * - Auto-transitions into main app after 1.8 seconds
 */
@Composable
fun SplashScreen(
    onSplashComplete: () -> Unit
) {
    val scale = remember { Animatable(0.85f) }
    val alpha = remember { Animatable(0.35f) }
    val pulseAlpha = remember { Animatable(0.2f) }

    LaunchedEffect(Unit) {
        // Run entry scale & fade-in animations concurrently
        scale.animateTo(
            targetValue = 1.0f,
            animationSpec = tween(durationMillis = 600, easing = FastOutSlowInEasing)
        )
    }

    LaunchedEffect(Unit) {
        alpha.animateTo(
            targetValue = 1.0f,
            animationSpec = tween(durationMillis = 500)
        )
    }

    LaunchedEffect(Unit) {
        pulseAlpha.animateTo(
            targetValue = 0.6f,
            animationSpec = infiniteRepeatable(
                animation = tween(durationMillis = 1000, easing = FastOutSlowInEasing),
                repeatMode = RepeatMode.Reverse
            )
        )
    }

    LaunchedEffect(Unit) {
        delay(1800)
        onSplashComplete()
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(BackgroundDark),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center,
            modifier = Modifier.padding(24.dp)
        ) {
            // Glowing Pulse Ring & Logo Container
            Box(
                contentAlignment = Alignment.Center,
                modifier = Modifier.size(180.dp)
            ) {
                // Pulse background ring
                Box(
                    modifier = Modifier
                        .size(170.dp)
                        .scale(scale.value * 1.05f)
                        .alpha(pulseAlpha.value)
                        .clip(CircleShape)
                        .background(PrimaryEmerald.copy(alpha = 0.25f))
                        .border(2.dp, PrimaryEmeraldLight.copy(alpha = 0.4f), CircleShape)
                )

                // Main Web App "VF" Logo Emblem
                Box(
                    contentAlignment = Alignment.Center,
                    modifier = Modifier
                        .size(130.dp)
                        .scale(scale.value)
                        .alpha(alpha.value)
                        .clip(RoundedCornerShape(32.dp))
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
                        fontSize = 52.sp,
                        letterSpacing = (-1.5).sp
                    )
                }
            }

            Spacer(modifier = Modifier.height(28.dp))

            // Title & Subtitle Fade-In
            Column(
                horizontalAlignment = Alignment.CenterHorizontally,
                modifier = Modifier.alpha(alpha.value)
            ) {
                Text(
                    text = "VeriFeed",
                    fontSize = 36.sp,
                    fontWeight = FontWeight.Bold,
                    color = TextPrimary,
                    letterSpacing = 1.sp
                )

                Spacer(modifier = Modifier.height(10.dp))

                // Capability Badge Pill
                Box(
                    modifier = Modifier
                        .clip(RoundedCornerShape(20.dp))
                        .background(PrimaryEmerald.copy(alpha = 0.15f))
                        .border(1.dp, PrimaryEmerald, RoundedCornerShape(20.dp))
                        .padding(horizontal = 16.dp, vertical = 6.dp)
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Box(
                            modifier = Modifier
                                .size(6.dp)
                                .clip(CircleShape)
                                .background(PrimaryEmerald)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "PROACTIVE PROTECTION • EVIDENCE-FIRST AI",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Bold,
                            color = PrimaryEmerald
                        )
                    }
                }

                Spacer(modifier = Modifier.height(48.dp))

                // Footer Loading Text
                Text(
                    text = "Initializing Threat Intelligence Engine…",
                    fontSize = 12.sp,
                    color = TextSecondary,
                    fontWeight = FontWeight.Medium
                )
            }
        }
    }
}
