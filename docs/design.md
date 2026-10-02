# 4. User Interface & Agent Interaction Design

This document specifies the persona guidelines, response formatting rules, verdict enums, and UI layout specifications for the **VeriFeed Malawian Information Verification, Truth Engine, and Fraud Prevention Platform**.

---

## 4.1 Persona & Output Rules

The AI Agent operates under strict persona and interaction directives:

- **Persona:** Acts as an objective, natural, and highly helpful verification officer.
- **Tone:** Concise, authoritative, direct, and reassuring. Avoids robotic template phrasing, corporate jargon, or hedging filler text ("Based on my search parameters...").
- **Truth Boundary:** Answers must be directly grounded in retrieved live evidence links and verified ground-truth vectors. Never guess or hallucinate facts.

---

## 4.2 Canonical Verdict Labels

All system responses must output a single canonical verdict enum value:

```typescript
type VerdictEnum =
  | "VERIFIED_TRUE"       // Confirmed accurate by official statements or media
  | "VERIFIED_FALSE"      // Confirmed false or debunked by authorities
  | "HIGH_RISK_SCAM"      // Phishing URL, domain spoof, or fraud scheme
  | "FORGED_DOCUMENT"     // Modified text surrounding official signature/seal
  | "IN_REVIEW";          // Unverified claim with no official coverage found
```

---

## 4.3 Standardized Response Structure

Every verification output presented to the user follows a 5-part structured format:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. HEADLINE VERDICT                                                         │
│    [ VERIFIED STATEMENT ] / [ WARNING: HIGH RISK FRAUD DETECTED ]           │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. DIRECT ANSWER                                                            │
│    Clear, immediate 1-2 sentence statement giving the core fact upfront.    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. EVIDENCE & CONTEXT BREAKDOWN                                             │
│    Detailed explanation citing live primary sources and official releases.  │
├─────────────────────────────────────────────────────────────────────────────┤
│ 4. LIVE URL PROOFS                                                          │
│    • https://www.gov.mw/press-release-1042                                  │
│    • https://www.zodiakmalawi.com/article-2910                              │
├─────────────────────────────────────────────────────────────────────────────┤
│ 5. ACTIONABLE CAUTION STEPS (Scam / Fraud Alerts Only)                      │
│    • Do NOT click the link or provide your mobile money PIN.                │
│    • Do NOT forward this message on WhatsApp or social media.               │
│    • Report the sender's phone number to customer support.                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Response Component Definitions

1. **Headline Verdict:**
   Clear badge or header displaying one of the 5 canonical verdicts (`VERIFIED_TRUE`, `VERIFIED_FALSE`, `HIGH_RISK_SCAM`, `FORGED_DOCUMENT`, `IN_REVIEW`).

2. **Direct Answer:**
   Immediate, clear answer providing the resolution without fluff.

3. **Evidence & Context Breakdown:**
   In-depth narrative explaining *why* the claim is true, false, forged, or unverified, referencing official statements, gazettes, or media releases.

4. **Live URL Proofs:**
   Clickable, verified Markdown links pointing directly to the primary sources found on whitelisted domains.

5. **Actionable Caution Steps:**
   Contextual security instructions provided whenever a claim is flagged as `HIGH_RISK_SCAM` or `FORGED_DOCUMENT` to protect the user against financial loss or identity theft.
