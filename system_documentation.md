# VeriFeed — Malawi Information Verification & Anti-Propaganda Platform
## Master System Specification Document

> This document is the **single source of truth** for the VeriFeed system architecture, algorithms, flows, and design decisions. All implementation must conform to this specification.

### 📚 Consolidated Modular Architecture Specifications
- 📘 [docs/algorithm.md](file:///home/graysoncomrademsiska/Documents/Development/WebDev/Python/Verifeed/docs/algorithm.md) — Dynamic Algorithm Specification (Multi-Modal Ingestion, Dual Retrieval, $S=0.35 S_{domain} + 0.35 S_{vector} + 0.20 S_{forensic} + 0.10 S_{telecom}$, Levenshtein Spoof Checks)
- 📐 [docs/blueprint.md](file:///home/graysoncomrademsiska/Documents/Development/WebDev/Python/Verifeed/docs/blueprint.md) — System Blueprint & Relational/Pgvector Database Schema
- 🔄 [docs/system_flow.md](file:///home/graysoncomrademsiska/Documents/Development/WebDev/Python/Verifeed/docs/system_flow.md) — End-to-End Execution Paths & Hard Rule Decision Trees
- 🎨 [docs/design.md](file:///home/graysoncomrademsiska/Documents/Development/WebDev/Python/Verifeed/docs/design.md) — User Interface, Persona Guidelines & Verdict Enums
- 💻 [docs/implementation.md](file:///home/graysoncomrademsiska/Documents/Development/WebDev/Python/Verifeed/docs/implementation.md) — Complete FastAPI Backend Reference Implementation

---

# 1. Mission & Product Vision

VeriFeed is a Malawi-focused platform designed to **eliminate the spread of propaganda, fake news, and fraud** by providing citizens with an instant, evidence-grounded verdict on any piece of information — message, document, image, link, or claim — before they act on it.

## 1.1 The Core Problem It Solves

| Problem | Example |
|---|---|
| Fake government memos circulating on WhatsApp | Fake civil servant promotion lists with forged official signatures |
| Staged strike & policy announcements | "Teachers striking tomorrow" — fabricated with fake MoE header |
| Telecom scam promotions | "You won MK500,000! Send MK200 to 0991234567 to claim — TNM" |
| Phishing links | "Click http://bit.ly/tnm-win to collect your Airtel reward" |
| Fake institutional news | Fabricated RBM, Standard Bank, Airtel Money press releases |
| Misinformation from influencers | Politicians or public figures making false claims |
| Fake promotions in Chichewa/mixed language | "Mwapambana! Tumizani MK500 kwa Mpamba" |

## 1.2 What VeriFeed is NOT

- ❌ VeriFeed is **not** the source of truth
- ❌ The AI agent is **not** a fact generator — it never invents information
- ❌ VeriFeed does **not** censor information — it adds a confidence label and evidence trail

---

# 2. The Truth Hierarchy (Source of Truth Architecture)

The system operates on a **tiered source-of-truth hierarchy**. Only registered and verified sources can anchor a verdict. The AI agent sits between the user and these sources.

```
TIER 1 — Highest Authority (Anchors verdicts definitively)
├── Government Ministries & MDAs (malawi.gov.mw, ministry sites)
├── Regulatory Bodies (RBM, MACRA, MRA, MERA)
├── Registered Telecom Operators (TNM, Airtel — official APIs/sites)
└── Registered Banks & Financial Institutions

TIER 2 — High Authority (Strong corroborating evidence)
├── Registered & Licensed Media Outlets
│   ├── Times 360 (times.mw)
│   ├── MBC TV (mbctv.mw)
│   ├── Malawi 24 (malawi24.com)
│   ├── Zodiak Broadcasting Station
│   ├── Nation Online (mwnation.com)
│   └── Nyasa Times (nyasatimes.com)
├── Fact-Check Organisations (Africa Check, FirstCheck Africa)
└── Verified Official Social Media Pages (Facebook Verified Pages, X Blue-tick accounts)
    of the above institutions

TIER 3 — Supporting Evidence (Can corroborate but not anchor)
├── Reputable Public Figures (ministers, MPs, governors — ONLY on verified accounts)
├── Verified Celebrities & Influencers (when speaking on their specialty)
└── Academic Institutions

TIER 4 — Community Signals (Cannot confirm — can only raise suspicion)
├── User Submissions & Reports
├── Submission Clusters (patterns across many reports)
└── Social media posts from unverified accounts
```

> [!IMPORTANT]
> **The Verdict Trust Boundary Rule:**
> `COMMUNITY REPORT ≠ CONFIRMED SCAM`
> `STAGE 1 SIGNAL ≠ VERIFIED EVIDENCE`
> `AI ANALYSIS ≠ FINAL VERDICT`
> Only Tier 1/Tier 2 evidence can produce a `VERIFIED_TRUE` or `VERIFIED_FALSE` verdict. Everything else produces `PENDING_VERIFICATION` or `UNVERIFIED`.

---

# 3. System Architecture & Components

## 3.1 Component Map

```
┌─────────────────────────────────────────────────────┐
│                   User Interfaces                    │
│  ┌──────────────────┐   ┌──────────────────────┐    │
│  │  Next.js Web App │   │  Android Mobile App  │    │
│  │  /verify         │   │  SMS / Notification  │    │
│  │  /scams          │   │  Share-to-Verify      │    │
│  │  /search         │   │  Fake Number Flagging│    │
│  └────────┬─────────┘   └──────────┬───────────┘    │
└───────────┼──────────────────────  ┼ ───────────────┘
            │                        │
            ▼                        ▼
┌────────────────────────────────────────────────────┐
│              FastAPI Gateway (v1)                   │
│  POST /api/v1/screen  — Stage 1: Fast Rule Check   │
│  POST /api/v1/verify  — Stage 2: Full RAG Pipeline │
│  POST /api/v1/verify/submit-scam — Community Report │
│  GET  /api/v1/verify/alerts — Institutional Alerts  │
│  POST /api/v1/verify/email — Email Phishing Check  │
└────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────┐
│         Processing & Forensic Pipeline              │
│  ┌────────────────┐  ┌──────────────────────────┐  │
│  │ Multi-Modal    │  │  Rule-Based Hard Check   │  │
│  │ Ingestion      │  │  (Inline, before RAG)    │  │
│  │ - OCR          │  │  - Scam keyword match    │  │
│  │ - pHash        │  │  - Domain blacklist      │  │
│  │ - PDF extract  │  │  - Phone registry check  │  │
│  │ - Regex NLP    │  │  → HIGH_RISK_SCAM exit   │  │
│  └────────────────┘  └──────────────────────────┘  │
└────────────────────────────────────────────────────┘
            │ (if no hard match)
            ▼
┌────────────────────────────────────────────────────┐
│         RAG Vector Search Engine                    │
│  PostgreSQL + pgvector (768-dim embeddings)         │
│  Searches:                                          │
│  - Institutional Alerts (Tier 1)                   │
│  - Indexed News Articles (Tier 2)                  │
│  - Fact-Check Ratings (Tier 2)                     │
│  - Signature Fingerprint Registry                  │
│  - Scam Pattern Database                           │
└────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────┐
│         Evidence Ranker & Confidence Scorer         │
│  S = 0.35·S_domain + 0.35·S_vector                 │
│      + 0.20·S_signature + 0.10·S_telecom            │
│  Ranks evidence by Tier hierarchy                   │
│  Builds human-readable methodology string           │
└────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────┐
│         AI Agent Reasoning Layer (Gemini)           │
│  ROLE: Inference & Explanation Engine ONLY          │
│  - Reads retrieved context blocks                   │
│  - NEVER uses parametric memory about Malawi        │
│  - Synthesizes verdict + summary in plain language  │
│  - Adds actionable_advice for user                  │
│  - Outputs: VERIFIED_TRUE | VERIFIED_FALSE |        │
│    HIGH_RISK_SCAM | PENDING_VERIFICATION | UNVERIFIED│
└────────────────────────────────────────────────────┘
            │
            ▼
┌────────────────────────────────────────────────────┐
│              Output Generation Layer                │
│  Returns structured JSON with:                      │
│  - verdict (canonical 5-label system)               │
│  - confidence (weighted float 0.0–0.99)             │
│  - claim_verdict (True/False/Misleading/etc)        │
│  - message_authenticity_verdict                     │
│  - summary (plain language, Chichewa-aware)         │
│  - official_sources [{name, url}]                   │
│  - actionable_advice (single imperative string)     │
│  - methodology (how verdict was reached)            │
└────────────────────────────────────────────────────┘
```

## 3.2 Ingestion & Scraper Engine

Scheduled background workers (Celery + Redis) that fetch and index ground-truth content:

| Worker | Source | Schedule | Priority |
|---|---|---|---|
| `govt_scraper` | malawi.gov.mw, ministry domains | Every 15 min | Highest |
| `telecom_scraper` | tnm.co.mw, airtel.mw | Every 15 min | Highest |
| `media_scraper` | times.mw, mbctv.mw, malawi24.com, mwnation.com, nyasatimes.com | Every 30 min | High |
| `rbm_scraper` | rbm.mw | Every 15 min | Highest |
| `macra_scraper` | macra.mw | Every 30 min | High |
| `fact_check_api` | Google Fact Check Tools API | On-demand | Medium |

---

# 4. The Canonical Algorithm

## 4.1 End-to-End Execution Flow

```
[User Input: Text / Image / PDF / Link / SMS / Memo]
                     │
                     ▼
    ┌─────────────────────────────────────┐
    │  Multi-Modal Ingestion Layer         │
    │  - If image/PDF: OCR + pHash        │
    │  - If text/URL: Regex extraction    │
    │  - Entity extraction:               │
    │    phones, URLs, USSD, sender ID,   │
    │    institution names, Chichewa kw   │
    └─────────────────────────────────────┘
                     │
                     ▼
    ┌─────────────────────────────────────┐
    │  STAGE 1: Rule-Based Hard Check     │ ◄─── Runs INLINE inside verify_claim()
    │  (Deterministic, <5ms, no AI)       │      NOT as a separate pre-step
    │                                     │
    │  Checks:                            │
    │  • Scam keyword match (EN + Chich.) │
    │  • Phishing domain/URL pattern      │
    │  • Lookalike domain detection       │
    │  • Phone number blacklist           │
    │  • Unsolicited prize language       │
    │  • Monetary transfer request        │
    └─────────────┬───────────────────────┘
                  │
         ┌────────┴─────────┐
         ▼                  ▼
  [HIGH_RISK_SCAM]    [No Hard Match]
  Fast Exit →         Continue →
  Persist log         Stage 2
  Return result
                          │
                          ▼
    ┌─────────────────────────────────────┐
    │  STAGE 2: Identity & Channel Check  │
    │  • Is the sender in official        │
    │    registry? (institution DB)       │
    │  • Does the USSD/short code match?  │
    │  • Is the domain official?          │
    │  → message_authenticity_verdict     │
    └─────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────┐
    │  STAGE 3: Signature Verification    │ ◄─── For image/PDF inputs
    │  (pHash Forensic Analysis)          │
    │  • Compute pHash of document        │
    │  • Compare against official         │
    │    signature fingerprint registry   │
    │  • Threshold ≤ 10 → match           │
    │  → S_signature score (0.0–1.0)      │
    └─────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────┐
    │  STAGE 4: RAG Vector Search         │
    │  (pgvector cosine similarity)       │
    │  • Search Institutional Alerts      │
    │  • Search Indexed News Articles     │
    │  • Search Fact-Check Ratings        │
    │  • Extract cosine_similarity float  │
    │  → S_vector score (0.0–1.0)         │
    └─────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────┐
    │  STAGE 5: Evidence Ranking          │
    │  Weighted Confidence Formula:       │
    │  S = 0.30·S_domain                  │
    │    + 0.40·S_vector                  │
    │    + 0.20·S_signature               │
    │    + 0.10·S_telecom                 │
    │  Tier hierarchy ranking             │
    │  Methodology string generation      │
    └─────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────┐
    │  STAGE 6: AI Agent Synthesis        │
    │  (Gemini — context-only, no memory) │
    │                                     │
    │  Prompt contains:                   │
    │  - STRICT: No parametric memory     │
    │  - USER CLAIM                       │
    │  - EXTRACTED ENTITIES               │
    │  - RANKED EVIDENCE BLOCKS           │
    │  - CHANNEL VERIFICATION RESULT      │
    │  - STAGE 1 SCREENING RESULT         │
    │                                     │
    │  If no context → UNVERIFIED (skip AI│
    │  call entirely)                     │
    └─────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────┐
    │  OUTPUT GENERATION                  │
    │  Canonical 5-label verdict:         │
    │  VERIFIED_TRUE | VERIFIED_FALSE |   │
    │  HIGH_RISK_SCAM | PENDING_VERIF. |  │
    │  UNVERIFIED                         │
    │                                     │
    │  Full response includes:            │
    │  - verdict (canonical)              │
    │  - confidence (0.0–0.99)            │
    │  - summary (plain language)         │
    │  - official_sources [{name, url}]   │
    │  - actionable_advice (string)       │
    │  - methodology                      │
    │  - claim_verdict                    │
    │  - message_authenticity_verdict     │
    │  - risk_level                       │
    │  - extracted entities               │
    └─────────────────────────────────────┘
```

## 4.2 Weighted Confidence Scoring (§3.1)

```
S = w1·S_domain + w2·S_vector + w3·S_signature + w4·S_telecom

Where:
  w1 = 0.30  S_domain    = Domain/Link Trust Score
  w2 = 0.40  S_vector    = RAG Vector Similarity Match Score
  w3 = 0.20  S_signature = Signature/pHash Alignment Score
  w4 = 0.10  S_telecom   = Phone/Telecom Blacklist Score

Sub-score computation:
  S_domain:
    1.0  → All URLs from official registered domains
    0.5  → Mixed (some official, some unknown)
    0.0  → Suspicious/blacklisted/shortened URL detected

  S_vector:
    cosine_similarity score from pgvector nearest-neighbour search
    Normalised: 0.0 (no match) → 1.0 (perfect match)
    Default 0.0 if no evidence retrieved

  S_signature:
    1.0  → pHash distance ≤ 10 (official signature match)
    0.5  → Image present but no signature registry match
    0.5  → No image input (neutral — not penalised)
    0.0  → pHash distance > 10 (forged/altered signature)

  S_telecom:
    1.0  → Sender/number in official institution registry (matched)
    0.5  → Unknown sender (not blacklisted, not official)
    0.0  → Sender/number in blacklist (SuspiciousSender DB)
```

## 4.3 Signature Verification Algorithm (§3.2 — pHash)

For images and PDF documents, especially government memos and institutional letters:

```python
import imagehash
from PIL import Image

def compute_signature_phash(image_data: str, bbox: tuple | None = None) -> str:
    """
    Decode base64 image, optionally crop to signature bounding box,
    compute perceptual hash (pHash).
    """
    image = Image.open(BytesIO(base64.b64decode(image_data)))
    if bbox:
        image = image.crop(bbox)  # (left, top, right, bottom)
    phash = imagehash.phash(image)
    return str(phash)

def verify_signature(document_phash: str, registered_hashes: list[str]) -> tuple[bool, float]:
    """
    Compare pHash distance. Threshold ≤ 10 = match.
    Returns (matched: bool, similarity_score: float 0.0-1.0)
    """
    for reg_hash in registered_hashes:
        distance = imagehash.hex_to_hash(document_phash) - imagehash.hex_to_hash(reg_hash)
        if distance <= 10:
            similarity = 1.0 - (distance / 64)  # normalized Hamming distance
            return True, round(similarity, 3)
    return False, 0.5  # no match but no penalty if registry is empty
```

## 4.4 Rule-Based Screening Engine — English + Chichewa

The rule engine runs **inline** inside `verify_claim()` BEFORE the RAG search.

### English Keywords
- **Urgency:** `act now`, `expires today`, `limited time`, `immediately`, `account suspended`, `verify now`
- **Monetary requests:** `send money`, `transfer funds`, `processing fee`, `activation fee`, `buy voucher`, `airtel money transfer`
- **Unsolicited prizes:** `you have won`, `claim your prize`, `lucky winner`, `cash prize`, `free iphone`
- **Impersonation:** `standard bank`, `airtel money`, `tnm mpamba`, `reserve bank`, `macra`, `malawi government`

### Chichewa / Mixed-Language Keywords
- **Prize lures:** `mwapambana`, `mupeze mphatso`, `mupeze ndalama`, `mwagonjetsa`
- **Monetary requests:** `tumizani ndalama`, `lipsani`, `pitani ku`, `mtumizeni`
- **Urgency:** `lowani mwachangu`, `nthawi yatha`, `chitani posachedwa`, `izi ndi zoona`
- **Promotions:** `mtukula pakhomo`, `kuwina`, `pusepa`, `pension`, `promo`, `claim`

### Suspicious URL Patterns
- Shortened links: `bit.ly`, `tinyurl.com`, `rb.gy`, `is.gd`, `cutt.ly`, `goo.gl`
- Typosquat of Malawian institutions: `airtel-mw.`, `standard-bank-mw.`, `tnm-mpamba.`, `rbm-mw.`, `malawi-gov.`, `mw-gov.`

---

# 5. Canonical Output Schema

```json
{
  "id": 42,
  "verdict": "VERIFIED_TRUE | VERIFIED_FALSE | HIGH_RISK_SCAM | PENDING_VERIFICATION | UNVERIFIED",
  "claim_verdict": "True | False | Partly True | Misleading | Insufficient Evidence",
  "message_authenticity_verdict": "Verified Official | Likely Legitimate | Unverified | Suspicious | Likely Fraudulent | Confirmed Fraudulent",
  "confidence": 0.87,
  "risk_level": "High | Medium | Low",
  "summary": "<Plain-language 2-4 sentence explanation. Must reference specific facts from evidence. Must be vivid — not generic.>",
  "official_sources": [
    {"name": "TNM Mpamba Official Notice", "url": "https://www.tnm.mw/security-notice"},
    {"name": "Times 360 Report", "url": "https://times.mw/..."}
  ],
  "actionable_advice": "<Single imperative sentence: what the user should do RIGHT NOW.>",
  "methodology": "<Human-readable explanation of how verdict was reached.>",
  "extracted_sender": "TNM | +265991000105 | AirtelMoney",
  "extracted_numbers": ["+265991234567"],
  "extracted_urls": ["https://bit.ly/fake-claim"],
  "extracted_institutions": ["TNM Mpamba", "Airtel Money"],
  "verification_details": {
    "sender_verified": false,
    "channel_verified": false,
    "matched_institution": "TNM Mpamba"
  },
  "recommended_actions": [
    {"action": "...", "priority": "critical | high | medium | low", "reason": "..."}
  ],
  "created_at": "2026-09-23T10:00:00"
}
```

### Verdict Label Definitions

| Canonical Label | When Used | Color Code |
|---|---|---|
| `VERIFIED_TRUE` | Tier 1/2 evidence confirms the claim is accurate | 🟢 Green |
| `VERIFIED_FALSE` | Tier 1/2 evidence directly contradicts or debunks the claim | 🔴 Red |
| `HIGH_RISK_SCAM` | Hard rule match: phishing URL, blacklisted number, monetary request + impersonation | 🔴 Red (pulsing) |
| `PENDING_VERIFICATION` | Some evidence exists but not sufficient to confirm or deny; needs more indexing | 🟡 Yellow |
| `UNVERIFIED` | Zero evidence retrieved from any source — cannot confirm or deny | ⚪ Grey |

### Legacy Verdict Mapping (backward compatibility)

| Legacy Label | Maps To |
|---|---|
| `Confirmed Scam` | `HIGH_RISK_SCAM` |
| `Confirmed` | `VERIFIED_TRUE` |
| `Disputed / False` | `VERIFIED_FALSE` |
| `Unconfirmed` | `PENDING_VERIFICATION` |
| `No Coverage Found` | `UNVERIFIED` |

---

# 6. Document Forgery Detection (Fake Memos)

Malawi-specific problem: fake government memos, promotion lists, strike notices circulating on WhatsApp with forged official letterheads and signatures.

## 6.1 Detection Pipeline

```
[User uploads image/PDF of a memo]
                │
                ▼
   ┌─────────────────────────────┐
   │  OCR Text Extraction         │
   │  - Extract all text          │
   │  - Extract headline          │
   │  - Extract reference numbers │
   │  - Extract date & ministry   │
   └─────────────────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  Signature Region Detection  │
   │  - Detect signature block    │
   │    (lower-right region bbox) │
   │  - Compute pHash of signature│
   │    region                    │
   └─────────────────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  Registry Comparison         │
   │  - Query SignatureFingerprint│
   │    registry for institution  │
   │  - pHash distance ≤ 10?      │
   │    → MATCH (S_signature=1.0) │
   │  - Distance > 10?            │
   │    → FORGED (S_signature=0.0)│
   └─────────────────────────────┘
                │
                ▼
   ┌─────────────────────────────┐
   │  RAG Cross-Reference         │
   │  - Query government news     │
   │    index for this memo topic │
   │  - Does official source      │
   │    corroborate the content?  │
   └─────────────────────────────┘
```

## 6.2 Signature Fingerprint Registry

```
SignatureFingerprints Table:
  id            UUID primary key
  institution_id  FK → institutions
  signatory_name  Name of official (e.g., "Secretary to the President")
  role           Official title
  phash_value   Computed pHash of official signature sample
  registered_by  Admin user
  registered_at  DateTime
  is_active     Boolean
```

---

# 7. Data Models (Entity Relationship)

```
┌─────────────────────────┐        ┌─────────────────────────┐
│     Source Registry     │        │     Document Embeddings  │
├─────────────────────────┤        ├─────────────────────────┤
│ id (UUID)               │1      *│ id (UUID)                │
│ name (e.g. Times 360)   ├───────►│ source_id (FK)           │
│ domain (e.g. times.mw)  │        │ content_chunk (Text)     │
│ trust_tier (1, 2, 3)    │        │ embedding (Vector 768)   │
│ is_verified (Bool)      │        │ document_type            │
└─────────────────────────┘        └─────────────────────────┘

┌─────────────────────────┐        ┌─────────────────────────┐
│     Institutions        │        │ Signature Fingerprints   │
├─────────────────────────┤        ├─────────────────────────┤
│ id (Int)                │1      *│ id (UUID)                │
│ name                    ├───────►│ institution_id (FK)      │
│ sector                  │        │ signatory_name           │
│ website_url             │        │ phash_value (String)     │
│ official_sms_sender_ids │        │ is_active (Bool)         │
│ official_phone_numbers  │        └─────────────────────────┘
│ official_short_codes    │
│ official_ussd_codes     │        ┌─────────────────────────┐
│ official_email_domains  │        │   Scam Registry          │
│ verified_social_accounts│        ├─────────────────────────┤
└─────────────────────────┘        │ SuspiciousSender         │
                                   │   phone/shortcode/id     │
┌─────────────────────────┐        │   report_count (Int)     │
│   VerificationLog        │        │   status                 │
├─────────────────────────┤        ├─────────────────────────┤
│ id (Int)                │        │ SuspiciousUrl            │
│ query_text              │        │   domain                 │
│ verdict (canonical)     │        │   report_count (Int)     │
│ claim_verdict           │        │   threat_type            │
│ msg_authenticity_verdict│        ├─────────────────────────┤
│ confidence_score        │        │ KnownScamPattern         │
│ risk_level              │        │   pattern_value          │
│ summary                 │        │   pattern_type           │
│ official_sources JSON   │        │   language (EN/Chich)    │
│ actionable_advice       │        └─────────────────────────┘
│ methodology             │
│ extracted_sender        │
│ extracted_numbers JSON  │
│ extracted_urls JSON     │
│ sender_verified (Bool)  │
│ channel_verified (Bool) │
│ recommended_actions JSON│
│ created_at              │
└─────────────────────────┘
```

---

# 8. AI Agent Specification (Gemini)

## 8.1 Role & Guardrails

- **Role:** Inference & Explanation Engine only — NOT a source of truth
- **Persona:** Objective, factual, concise, neutral public verification officer
- **Languages:** Standard English, Chichewa, and mixed Chinglish/Nyanja context understanding
- **STRICT RULE:** Never use parametric pre-training memory to state factual claims about Malawi news, memos, or promotions. Only evaluate retrieved context blocks.
- **UNVERIFIED trigger:** If zero context blocks are retrieved, return `UNVERIFIED` without calling Gemini (deterministic skip).

## 8.2 System Prompt Template

```text
SYSTEM INSTRUCTION:
You are the VeriFeed Truth Verification Assistant for Malawi.
Your ONLY role is to evaluate user claims against the provided CONTEXT BLOCKS.

STRICT CONSTRAINTS:
1. Do NOT use external pre-trained knowledge to state factual truths
   regarding news, memos, promotions, or policies in Malawi.
2. Rely ONLY on the provided CONTEXT BLOCKS below.
3. If no relevant CONTEXT BLOCKS are provided, set verdict to "UNVERIFIED"
   and state: "Official confirmation is currently unavailable in VeriFeed's index."
4. Your summary must be vivid and specific — synthesize the actual facts
   from the evidence. NEVER write generic responses like "Found 2 alerts."
   Instead, explain WHAT the alerts say and WHY the user should act.
5. actionable_advice must be a single imperative sentence.

INPUT FORMAT:
  Query/Claim: {USER_CLAIM}
  Extracted Entities: {ENTITIES}
  Stage 1 Screening Result: {SCREENING_RESULT}
  Channel Verification: {CHANNEL_VERIFICATION}
  Ranked Evidence Blocks: {RETRIEVED_DOCUMENTS}

OUTPUT FORMAT (strict JSON):
{
  "verdict": "<VERIFIED_TRUE | VERIFIED_FALSE | HIGH_RISK_SCAM | PENDING_VERIFICATION | UNVERIFIED>",
  "confidence_score": <float 0.0 to 1.0>,
  "summary": "<vivid 2-4 sentence explanation citing specific facts>",
  "actionable_advice": "<single imperative sentence>"
}
```

---

# 9. Mobile App Specification (Android)

## 9.1 Feature Scope

| Feature | Phase | Notes |
|---|---|---|
| Manual text/URL/image verification | E (MVP) | Core feature |
| Screenshot upload & verify | E (MVP) | Gallery + camera |
| Share-to-VeriFeed (intent receiver) | E (MVP) | ACTION_SEND intent filter |
| Offline Stage 1 local screening | E (MVP) | Regex/heuristic — no network needed |
| Investigation history | E (MVP) | JSON file store (Room later) |
| Fake number flagging in contacts | E (MVP) | Against SuspiciousSender registry |
| Notification screening | F (Policy-gated) | NotificationListenerService — explicit Play Store approval |
| Call screening | G (Later) | Requires default phone app |

## 9.2 Offline-First Architecture

```
Android App
   ├── Stage 1: LOCAL screening engine (Kotlin regex — zero network)
   │     Same signal logic as Python LocalScreeningEngine
   │     Malawi-specific: Chichewa keywords, TNM/Airtel patterns
   │
   └── Stage 2: API call → POST /api/v1/screen → POST /api/v1/verify
         Graceful degradation: if no network → show Stage 1 result only
```

## 9.3 Verdict UI Color Coding

| Verdict | Display | Mobile Notification |
|---|---|---|
| `VERIFIED_TRUE` | 🟢 Green banner — verified badge + official link | ✅ Safe |
| `VERIFIED_FALSE` | 🔴 Red banner — debunk statement + source | ⚠️ False — do not share |
| `HIGH_RISK_SCAM` | 🔴 Red pulsing banner — bold warning | 🚨 SCAM ALERT |
| `PENDING_VERIFICATION` | 🟡 Yellow badge — "under review" notice | ⏳ Not yet confirmed |
| `UNVERIFIED` | ⚪ Grey badge — "no official source yet" | ❓ Cannot verify |

---

# 10. Web Frontend Specification

## 10.1 Verify Flow

```
User visits /verify
    │
    ├── Input Method:
    │     ├── Text/SMS paste
    │     ├── URL paste
    │     ├── Image/Screenshot upload
    │     ├── PDF upload
    │     └── Pre-filled via ?content= URL param (share flow)
    │
    ├── Stage 1 (instant, <1s):
    │     QuickScreenWidget → POST /api/v1/screen
    │     Shows risk badge + signals immediately
    │     "Verify with VeriFeed →" CTA if needs_deep_verify
    │
    └── Stage 2 (3-10s):
          POST /api/v1/verify
          VerdictFirstResult renders:
            - Canonical verdict badge (new 5-label system)
            - Confidence indicator
            - Vivid summary
            - Official sources list (name + URL)
            - Actionable advice (bold, prominent)
            - Methodology
            - Extracted entities
            - Recommended actions
```

## 10.2 VerdictBadge Component — Canonical Label Mapping

The `VerdictBadge` component must handle BOTH the new canonical labels AND the legacy labels (for old DB records):

```
VERIFIED_TRUE        → Green   ✅
VERIFIED_FALSE       → Red     🚫
HIGH_RISK_SCAM       → Red     🛑 (pulsing)
PENDING_VERIFICATION → Yellow  ⚠️
UNVERIFIED           → Grey    ❓
```

---

# 11. API Endpoint Specification

## 11.1 Stage 1 — Immediate Screen

```
POST /api/v1/screen/
Body: { "content": string, "content_type": "message|url|email" }
Response: {
  "risk_level": "Low|Medium|High",
  "signals": [{signal_type, description, matched_text, severity}],
  "pattern_matches": [string],
  "needs_deep_verify": bool,
  "recommended_action": string,
  "screened_urls": [string],
  "detected_institutions": [string]
}
```

## 11.2 Stage 2 — Full Verification

```
POST /api/v1/verify/
Body: {
  "query": string | null,
  "image_data": base64string | null,
  "file_name": string | null,
  "prior_screening": ScreeningResult | null
}
Response: CanonicalVerificationResponse (see §5)
```

## 11.3 Community Scam Report

```
POST /api/v1/verify/submit-scam
Body: { "text": string | null, "image_data": base64 | null }
Response: { status, submission_id, cluster_id }
NOTE: Submission ≠ Confirmation. Community report only clusters signals.
```

## 11.4 Institutional Alerts Feed

```
GET /api/v1/verify/alerts?skip=0&limit=20
Response: [{id, title, alert_text, source_url, published_date, institution}]
```

---

# 12. Scraper & Ingestion Workers

```python
# Celery task — scheduled every 15 minutes
@celery_app.task
async def scrape_government_portals():
    sources = [
        "https://www.malawi.gov.mw/news",
        "https://www.rbm.mw/press-releases",
        "https://www.macra.org.mw/media",
        "https://www.tnm.co.mw/news",
        "https://www.airtel.mw/news",
    ]
    for url in sources:
        content = await fetch_and_parse(url)
        embedding = get_embedding(content.text)
        upsert_article(source_url=url, content=content, embedding=embedding)

@celery_app.task
async def scrape_news_outlets():
    sources = [
        "https://times.mw/category/news",
        "https://malawi24.com/news",
        "https://www.mwnation.com",
        "https://nyasatimes.com",
        "https://www.zodiak.mw",
    ]
    # Same pattern: fetch → parse → embed → upsert
```

---

# 13. Privacy & Permission Architecture

- **Never** request sensitive permissions before the feature requiring them is activated
- Stage 1 local screening operates entirely offline — no data leaves the device
- Stage 2 content is transmitted to the VeriFeed API over HTTPS only
- No notification content is stored server-side without explicit per-notification user consent
- Community submissions are anonymised before clustering
- Investigation history is stored locally on device only (no server sync until authenticated)

---

# 14. Implementation Phases (High-Level)

| Phase | Scope | Gate |
|---|---|---|
| A | Harden current web MVP, fix test coverage | All tests green, build passes |
| B | Staged verification pipeline (Stage 1 + Stage 2 separation) | Stage 1 smoke test passes |
| C | Proactive protection UI (QuickScreenWidget, ProtectionAlert) | Web build + e2e pass |
| D | Evidence pipeline (EvidenceRanker, methodology, dual-verdicts) | Verification agent tests pass |
| **E** | Android MVP (manual verify, screenshot, share-to-verify, local engine) | APK builds, unit tests pass |
| **F** | Notification screening (policy-gated) | Play policy approved |
| **G** | Call screening (later) | Deferred |
| **H** | Email OAuth connectors (later) | Deferred |
| **I** | iOS companion (after Android stable) | Deferred |

---

*This document is updated as the authoritative specification. All code must implement exactly the flows, formulas, and schemas defined here.*