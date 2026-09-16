package com.example.verifeed_android_app.ui.theme

import androidx.compose.ui.graphics.Color

// --- Darkish Baseline & Vibrant Emerald Palette ---------------------------

val BackgroundDark = Color(0xFF09120E)    // Deep dark emerald black
val SurfaceDark = Color(0xFF101E19)       // Main container dark surface
val CardDark = Color(0xFF162922)          // Sleek card container
val SurfaceInnerDark = Color(0xFF0C1713)   // Inner text input container

// Vibrant Emerald Green Accents
val PrimaryEmerald = Color(0xFF10B981)      // Main primary green
val PrimaryEmeraldDark = Color(0xFF059669)  // Darker emerald for pressed states
val PrimaryEmeraldLight = Color(0xFF34D399) // Bright emerald highlight / glow
val PrimaryEmeraldSubtle = Color(0xFF1A382C)// Subtle emerald tint background

// Text Tokens
val TextPrimary = Color(0xFFF9FAFB)
val TextSecondary = Color(0xFF9CA3AF)
val TextMuted = Color(0xFF6B7280)

// Borders
val BorderDark = Color(0xFF223C32)
val BorderEmerald = Color(0xFF10B981)
val BorderEmeraldSubtle = Color(0xFF1E4235)

// --- VeriFeed Semantic Verdict & Risk Colors -----------------------------

val VerdictGreen = Color(0xFF10B981)
val VerdictAmber = Color(0xFFF59E0B)
val VerdictRed = Color(0xFFEF4444)
val VerdictBlue = Color(0xFF3B82F6)

val RiskLowColor = Color(0xFF10B981)
val RiskMediumColor = Color(0xFFF59E0B)
val RiskHighColor = Color(0xFFEF4444)
val RiskUnknownColor = Color(0xFF6B7280)

// Legacy alias compatibility
val Primary700 = PrimaryEmerald
val Primary600 = PrimaryEmerald
val Primary500 = PrimaryEmeraldLight
val Ink900 = TextPrimary
val Ink500 = TextSecondary
val Danger = VerdictRed
val Success = VerdictGreen
val Warning = VerdictAmber
val Surface = SurfaceDark
val Background = BackgroundDark
val Border = BorderDark