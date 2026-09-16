package com.example.verifeed_android_app.ui.theme

import android.app.Activity
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkishColorScheme = darkColorScheme(
    primary = PrimaryEmerald,
    onPrimary = BackgroundDark,
    primaryContainer = PrimaryEmeraldSubtle,
    onPrimaryContainer = PrimaryEmeraldLight,
    secondary = PrimaryEmeraldLight,
    onSecondary = BackgroundDark,
    background = BackgroundDark,
    onBackground = TextPrimary,
    surface = SurfaceDark,
    onSurface = TextPrimary,
    surfaceVariant = CardDark,
    onSurfaceVariant = TextSecondary,
    outline = BorderDark,
    outlineVariant = BorderEmeraldSubtle,
    error = VerdictRed,
    onError = TextPrimary,
)

@Composable
fun VerifeedandroidappTheme(
    darkTheme: Boolean = true, // Default to sleek darkish theme per user requirement
    dynamicColor: Boolean = false,
    content: @Composable () -> Unit
) {
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = BackgroundDark.toArgb()
            window.navigationBarColor = SurfaceDark.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = false
        }
    }

    MaterialTheme(
        colorScheme = DarkishColorScheme,
        typography = Typography,
        content = content
    )
}