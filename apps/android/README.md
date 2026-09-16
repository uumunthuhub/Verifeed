# VeriFeed Android App (`apps/android`)

Android mobile companion focused on rapid fraud detection, SMS phishing screening, and evidence-first claim verification.

---

## 🛠️ Stack & Architecture

- **Language & UI:** Kotlin 2.0 + Jetpack Compose (Material3 dark theme)
- **Networking:** OkHttp 4.12.0
- **Build Tool:** Gradle 8.14.5 + AGP 8.13.2 (Offline Gradle Build support)
- **Minimum SDK:** API 26 (Android 8.0) | Target SDK: API 36

---

## 📱 Features & Screens

- **Verify Screen (`VerifyScreen.kt`):** Sleek AI Agent Container chat widget with attachment preview badge, sample prompt chips, fast on-device scan (Stage 1), and deep AI verification (Stage 2).
- **Stage 1 Screening (`ScreeningResultCard.kt`):** Instant on-device risk assessment badge (Low / Medium / High), signal pills, and recommended actions.
- **Stage 2 Verdict Report (`VerificationResultScreen.kt`):** Dual-verdict display (Claim Verdict + Authenticity Verdict), confidence meter bar, extracted entities, and ranked evidence sources.
- **Investigation History (`HistoryScreen.kt`):** Reverse-chronological local history list backed by thread-safe JSON file storage.
- **Privacy & Permission Controls (`SettingsScreen.kt`):** Granular permission inventory, deep verification toggle, remote Stage 1 toggle, and local data wiper.
- **Notification Screening Scaffold (`VeriFeedNotificationListener.kt`):** Opt-in `NotificationListenerService` for SMS, WhatsApp, Gmail, and Telegram.

---

## 🧪 Testing & Build

```bash
# Run Kotlin JVM unit tests
./gradlew test --offline

# Build debug APK
./gradlew assembleDebug --offline
```
