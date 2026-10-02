# VeriFeed Backend API (`apps/api`)

FastAPI backend service powering the VeriFeed evidence-first investigation engine, dual-verdict verification pipeline, local threat screening, and fraud intelligence domain.

---

## 🛠️ Stack & Technologies

- **Framework:** FastAPI + Pydantic v2
- **Database:** PostgreSQL + SQLAlchemy 2.0 ORM + Alembic migrations
- **Vector Search:** `pgvector` for semantic article & scam pattern matching
- **Task Queue & Workers:** Celery + Redis
- **AI Synthesis:** Google Gemini AI SDK (`google-genai`)
- **Package Manager:** `uv`

## Evidence Source Governance

The database source registry is the only place an automated ingestion job may read from. A source begins inactive and must be approved by an administrator before ingestion. Each active source records its approved content domains, trust tier, polling interval, ingestion status, and the provenance of every indexed article.

Use `PUT /api/v1/sources/{source_id}/registry` with the `X-Admin-Token` header to approve a validated feed. The token is supplied by `ADMIN_INGESTION_TOKEN`; if it is absent, registry-changing endpoints fail closed. A source URL must be HTTPS and every indexed article must belong to one of that source's approved domains.

Use `POST /api/v1/sources/scrape` only for a validated URL from an active source. This supports official publication pages that do not expose an RSS feed. Community submissions are kept separate from the approved evidence index and cannot independently produce a factual verdict.

---

## 📡 API Endpoints

### 1. Stage 1 Fast Threat Screening
- `POST /api/v1/screen`
  - **Body:** `{"content": "string", "content_type": "message|url|email"}`
  - **Returns:** `{ "risk_level": "Low|Medium|High", "signals": [...], "needs_deep_verify": bool }`
  - Near-instant deterministic rule matching without Gemini latency.

### 2. Stage 2 Deep Verification
- `POST /api/v1/verify`
  - **Body:** `{"query": "string", "image_data": "base64", "prior_screening": {...}}`
  - **Returns:** Full `VerificationResponse` including `claim_verdict`, `message_authenticity_verdict`, `confidence_score`, `sources[]`, `extracted_entities`, `methodology`, and `recommended_actions`.

### 3. Community Scam Reporting
- `POST /api/v1/verify/submit-scam`
  - **Body:** `{"text": "string", "category": "phishing"}`
  - Logs community scam reports to the fraud intelligence clustering engine.

---

## 🧪 Testing

```bash
# Run backend pytest suite
uv run pytest
```
- Total tests: **154 passed**
