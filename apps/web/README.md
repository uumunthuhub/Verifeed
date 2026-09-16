# VeriFeed Web Application (`apps/web`)

Next.js 16 + React 19 web application for proactive claim investigation, evidence browsing, scam pattern discovery, and real-time protection alerts.

---

## 🛠️ Stack & Components

- **Framework:** Next.js 16 (App Router) + React 19
- **Styling:** Tailwind CSS 4 + shadcn/ui design primitives
- **Testing:** Vitest + React Testing Library + Playwright e2e

---

## 🎨 Components & Flows

- `AskAgent.tsx`: Sleek AI agent container with quick sample prompts and image attachment preview.
- `QuickScreenWidget.tsx`: Real-time Stage 1 local screening widget.
- `ProtectionAlert.tsx`: Real-time banner alert when high-risk phishing/scam lures are detected.
- `VerdictFirstResult.tsx`: Dual-verdict renderer showing claim verdict, authenticity verdict, confidence meter, and ranked evidence sources.
- `EvidenceCard.tsx`: Individual evidence source card with credibility badges and external links.

---

## 🧪 Testing

```bash
# Unit test suite
pnpm test --run
```
- Total unit tests: **71 passed** (7 test suites)
