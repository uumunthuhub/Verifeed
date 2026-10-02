# 3. System Flowcharts & Execution Paths

This document provides detailed sequence diagrams, execution flowcharts, and branch handling for the **VeriFeed Malawian Information Verification, Truth Engine, and Fraud Prevention Platform**.

---

## 3.1 End-to-End System Execution Flow

```
[ User Input (Prompt / Image / Audio / SMS) ]
                     │
                     ▼
       ┌───────────────────────────┐
       │ Multi-Modal Preprocessor  │ ──► Run OCR / Speech-to-Text / Regex Extraction
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │   Hard Rule Evaluator     │ ──► Checks Lookalike Domains / Scam Numbers / Signature Forgery
       └─────────────┬─────────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
  [ Hard Flag Found ]   [ No Hard Flag ]
         │                       │
         │                       ▼
         │           ┌───────────────────────────┐
         │           │   Live Search & Vector    │ ──► Search Live Whitelisted Domains
         │           │      Retrieval Engine     │     and Pgvector Index
         │           └───────────┬───────────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │  Constrained AI Agent     │ ──► Synthesizes verdict, reasoning, and live links
       └─────────────┬─────────────┘
                     │
                     ▼
       ┌───────────────────────────┐
       │ User Presentation Layer   │ ──► Displays Clear Verdict + Direct URL Proofs
       └───────────────────────────┘
```

---

## 3.2 Detailed Sequential Flowchart (Mermaid)

```mermaid
sequenceDiagram
    autonumber
    actor User as User / App Client
    participant Pre as Multi-Modal Preprocessor
    participant Rule as Hard Rule Evaluator
    participant Ret as Retrieval Engine (Search + Pgvector)
    participant Agent as Constrained AI Agent
    participant UI as User Presentation Layer

    User->>Pre: Submit Prompt, Image Screenshot, Audio Note, or Shortlink
    Pre->>Pre: Extract Text via OCR (Image) / Whisper (Audio) / Regex (URLs & Phone Numbers)
    Pre->>Rule: Pass Extracted Entities & Signatures
    
    alt Hard Trigger Match (Levenshtein Distance 0 < d <= 3 OR Forged Signature pHash)
        Rule-->>UI: Immediate Fast-Exit Return (HIGH_RISK_SCAM / FORGED_DOCUMENT)
    else Clean / No Hard Trigger Match
        Rule->>Ret: Query Whitelisted Domains & Pgvector Vector DB
        Ret-->>Agent: Return Live Evidence Context & Top Vector Matches
        Agent->>Agent: Ground Verdict strictly on Retrieved Evidence (No Parametric Assumptions)
        Agent-->>UI: Return Final Verification Response (VERIFIED_TRUE / VERIFIED_FALSE / IN_REVIEW)
    end
    
    UI-->>User: Display Headline Verdict, Direct Answer, Live URL Proofs & Caution Steps
```

---

## 3.3 Branching Decision Tree

| Input Condition | Evaluator Rule | Execution Path | Verdict Outcome |
| :--- | :--- | :--- | :--- |
| Spoofed URL (e.g. `tnm-promo.com`) | Levenshtein dist $0 < d \le 3$ to official domain | Fast Exit | `HIGH_RISK_SCAM` (Confidence 1.00) |
| Press release with altered text but valid official crest | pHash matches signature seal, OCR body text missing from index | Fast Exit | `FORGED_DOCUMENT` (Confidence 1.00) |
| Claim matches official ministry announcement on `gov.mw` or `times.mw` | Live search & Pgvector return verified grounding links | AI Agent Grounding | `VERIFIED_TRUE` (Confidence 0.90+) |
| Rumor refuted by official statements or police reports | Live search returns refutation news | AI Agent Grounding | `VERIFIED_FALSE` (Confidence 0.90+) |
| Unverified social media post with zero web coverage | No matching articles or statements found in whitelisted index | AI Agent Safety | `IN_REVIEW` (Confidence 0.00) |
