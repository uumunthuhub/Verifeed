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
