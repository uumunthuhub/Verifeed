# VeriFeed — Proactive Misinformation & Fraud Protection Platform

[![VeriFeed Backend](https://img.shields.io/badge/API-FastAPI%20%2B%20SQLAlchemy-009688)](file:///home/graysoncomrademsiska/Documents/Development/WebDev/Python/Verifeed/apps/api)
[![VeriFeed Web](https://img.shields.io/badge/Web-Next.js%2016%20%2B%20React%2019-000000)](file:///home/graysoncomrademsiska/Documents/Development/WebDev/Python/Verifeed/apps/web)
[![VeriFeed Android](https://img.shields.io/badge/Android-Kotlin%20%2B%20Jetpack%20Compose-3DDC84)](file:///home/graysoncomrademsiska/Documents/Development/WebDev/Python/Verifeed/apps/android)

VeriFeed transforms claim verification from a **reactive** fact-checking website into a **proactive protection + on-demand verification** platform across Web and Mobile.

> **The Core Workflow:**
> `RECEIVE` ➔ `DETECT` ➔ `WARN` ➔ `VERIFY` ➔ `EVIDENCE` ➔ `UNDERSTAND` ➔ `ACT SAFELY`

---

## 🌟 Key Architecture & Capabilities

### 1. Two-Stage Verification Pipeline
- **Stage 1 (Fast On-Device / Threat API Screening):** Immediate (<100ms) deterministic heuristic screening. Scans urgency language, monetary requests, impersonations, suspicious short-codes, and URLs without wait latency.
- **Stage 2 (Deep Investigation Pipeline):** Triggered when deep verification is requested. Normalizes input, extracts entities, retrieves evidence from trusted institutional and fact-checking registries, and synthesizes grounded verdicts using Gemini AI.

### 2. Dual-Verdict System
Every deep investigation result provides two clear, distinct verdicts:
1. **Factual Claim Verdict:** Accuracy of the underlying statement (`TRUE`, `FALSE`, `MISLEADING`, `UNVERIFIED`).
2. **Message Authenticity Verdict:** Legitimacy of the communication channel (`AUTHENTIC`, `PHISHING / SCAM LURE`, `IMPERSONATION`, `SUSPICIOUS`).

### 3. Evidence-First Integrity
- **Grounding Principle:** Gemini AI does not determine verdicts from memory alone. Findings must be supported by retrieved evidence sources with clear source credibility scoring and methodology reasoning.

### 4. Incremental Privacy & Permission Architecture
- **Permission-Minimized:** VeriFeed never requests sensitive OS permissions up front.
- **Opt-in Proactive Protection:** `NotificationListenerService` scaffold on Android monitors messaging apps (SMS, WhatsApp, Gmail, Telegram) locally without storing raw notification text server-side.

---

## 📄 Real-World Scenario: Forwarded Memos & Public Notices

A primary core use-case addressed by VeriFeed is verifying **unverified public notices, civil servant memos, or government announcements circulating on WhatsApp and social media**.

### The Scenario
A citizen or pensioner receives a forwarded text or screenshot claiming:
> *"NOTICE TO ALL PENSIONERS IN MALAWI: Due to technical challenges affecting the pension disbursement system, pension payments will not be accessed today... Signed: PUSEPA PRESIDENT"*

### How VeriFeed Resolves It
```
[ RECEIVE ] ──► User pastes text or shares screenshot into VeriFeed (via Android Share Sheet or Web UI)
[ STAGE 1 ] ──► Instant screening (<100ms) flags high-impact keywords (PUSEPA, Pension Disbursement, System Downtime)
[ STAGE 2 ] ──► Entity Extraction isolates entities: PUSEPA, Government of Malawi, Genesis Malijana, Sep 14-16 dates
[ EVIDENCE ] ──► Queries official Ministry registries & verified news outlets (e.g., Zodiak TV, Times 360, BBC)
[ DUAL     ] ──► Factual Claim Verdict: UNVERIFIED / PENDING OFFICIAL STATEMENT
  VERDICT   ──► Message Authenticity Verdict: UNVERIFIED FORWARDED MEMO (Not sent from official gov domain/channel)
[ ACTION   ] ──► Clear User Guidance: "Cross-reference with Ministry of Finance official channels. Do not forward unverified WhatsApp messages."
```

---

## 📁 Repository Structure

```
VeriFeed/
├── apps/
│   ├── api/          # FastAPI + SQLAlchemy + PostgreSQL (pgvector) + Celery + Gemini AI
│   ├── web/          # Next.js 16 + React 19 + Tailwind CSS 4 + shadcn/ui
│   └── android/      # Android Kotlin app shell (Jetpack Compose, OkHttp, Local Engine)
├── database/         # Database seeds, scam pattern registries, and Alembic migrations
├── docker-compose.yml# Local development services (PostgreSQL + Redis + Celery)
└── README.md         # Monorepo documentation
```

---

## 🚀 Quick Start

### 1. Prerequisites
- **Docker & Docker Compose**
- **Python 3.12+** with `uv` package manager
- **Node.js 20+** with `pnpm`
- **Java 21 / Android SDK 34+** (for Android app builds)

### 2. Backend Services (`apps/api`)
```bash
# Start PostgreSQL (pgvector) & Redis
docker compose up -d

# Install Python dependencies and run API server
cd apps/api
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```
- API Health Check: `http://localhost:8000/health`
- Interactive OpenAPI Docs: `http://localhost:8000/docs`

### 3. Web Frontend (`apps/web`)
```bash
cd apps/web
pnpm install
pnpm dev
```
- Web Application: `http://localhost:3000`

### 4. Android Mobile Companion (`apps/android`)
```bash
cd apps/android
./gradlew test --offline           # Run JVM unit tests
./gradlew assembleDebug --offline  # Build debug APK
```

---

## 🧪 Testing & Quality Gates

Each layer enforces mandatory quality gates before deployment:

| Workspace | Test Command | Coverage Scope |
|---|---|---|
| **`apps/api`** | `cd apps/api && uv run pytest` | API Endpoints, Local Screening, Fraud Detector, Evidence Ranker, Verification Agent (154 tests) |
| **`apps/web`** | `cd apps/web && pnpm test --run` | EvidenceCard, ProtectionAlert, QuickScreenWidget, VerdictBadge, VerdictFirstResult (71 tests) |
| **`apps/android`** | `cd apps/android && ./gradlew test --offline` | LocalScreeningEngine, UrlExtractor, FileHistoryStore, ApiJsonParsing, NotificationListener |

---

## 🛡️ License

Built for evidence-first trust, misinformation defense, and fraud protection. All rights reserved.
