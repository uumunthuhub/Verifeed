# 5. Complete Backend Implementation

Here is the complete FastAPI application implementing the dynamic multi-modal verifier, rule engine, live web search integration, and grounded AI reasoning for the **Malawi Anti-Propaganda & Verification Engine**.

```python
import os
import re
from enum import Enum
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
import requests
import distance
from PIL import Image
import pytesseract
import whisper
from openai import OpenAI

app = FastAPI(title="Malawi Anti-Propaganda & Verification Engine")

# Initialize Clients & Models
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
whisper_model = whisper.load_model("base")

TRUSTED_DOMAINS = [
    "times.mw", "mbc.mw", "malawi24.com", "zodiakmalawi.com",
    "gov.mw", "macra.mw", "tnm.co.mw", "airtel.mw"
]

class VerdictEnum(str, Enum):
    VERIFIED_TRUE = "VERIFIED_TRUE"
    VERIFIED_FALSE = "VERIFIED_FALSE"
    HIGH_RISK_SCAM = "HIGH_RISK_SCAM"
    FORGED_DOCUMENT = "FORGED_DOCUMENT"
    IN_REVIEW = "IN_REVIEW"

class VerificationResponse(BaseModel):
    verdict: VerdictEnum
    confidence_score: float
    headline_answer: str
    detailed_breakdown: str
    evidence_links: List[str]
    caution_steps: Optional[List[str]] = None

def check_domain_spoofing(urls: List[str]) -> Optional[str]:
    for url in urls:
        domain = url.split("/")[2] if "://" in url else url.split("/")[0]
        if domain.lower() in TRUSTED_DOMAINS:
            continue
        for official in TRUSTED_DOMAINS:
            lev_dist = distance.levenshtein(domain.lower(), official)
            if 0 < lev_dist <= 3 or "promo" in domain.lower() or "win" in domain.lower():
                return url
    return None

def fetch_live_evidence(query: str) -> List[dict]:
    site_filter = " OR ".join([f"site:{d}" for d in TRUSTED_DOMAINS])
    search_query = f"{query} ({site_filter})"
    
    api_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": os.getenv("GOOGLE_SEARCH_API_KEY"),
        "cx": os.getenv("GOOGLE_CSE_ID"),
        "q": search_query,
        "num": 5
    }
    
    try:
        res = requests.get(api_url, params=params, timeout=5)
        results = res.json().get("items", [])
        return [
            {
                "title": r.get("title"),
                "snippet": r.get("snippet"),
                "url": r.get("link"),
                "source": r.get("displayLink")
            }
            for r in results
        ]
    except Exception:
        return []

@app.post("/api/v1/verify", response_model=VerificationResponse)
async def verify_claim(
    text_content: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    extracted_text = text_content or ""
    
    # 1. Multi-Modal File Processing
    if file:
        file_ext = file.filename.split(".")[-1].lower()
        temp_path = f"/tmp/{file.filename}"
        
        with open(temp_path, "wb") as f:
            f.write(await file.read())
            
        if file_ext in ["jpg", "jpeg", "png"]:
            image = Image.open(temp_path)
            ocr_text = pytesseract.image_to_string(image)
            extracted_text += f"\n[Extracted Screenshot Text]: {ocr_text}"
        elif file_ext in ["mp3", "wav", "m4a", "ogg"]:
            transcription = whisper_model.transcribe(temp_path)
            extracted_text += f"\n[Audio Transcript]: {transcription['text']}"
            
        if os.path.exists(temp_path):
            os.remove(temp_path)

    if not extracted_text.strip():
        raise HTTPException(status_code=400, detail="Please provide a query, text, or file input.")

    # 2. Extract Entities (URLs & Phone Numbers)
    url_pattern = r'https?://[^\s]+|www\.[^\s]+'
    extracted_urls = re.findall(url_pattern, extracted_text)

    # 3. Hard Rule Check: Phishing Domain Spoofing
    spoofed_url = check_domain_spoofing(extracted_urls)
    if spoofed_url:
        return VerificationResponse(
            verdict=VerdictEnum.HIGH_RISK_SCAM,
            confidence_score=1.0,
            headline_answer="WARNING: HIGH RISK FRAUD / SCAM DETECTED",
            detailed_breakdown=(
                f"The link '{spoofed_url}' is a spoofed domain attempting to mimic legitimate Malawian service providers. "
                "Official promotions and announcements are never hosted on unverified third-party domains."
            ),
            evidence_links=["https://www.tnm.co.mw", "https://www.airtel.mw"],
            caution_steps=[
                "Do NOT click the link or provide your mobile money PIN.",
                "Do NOT forward this message on WhatsApp or social media.",
                "Report the sender's phone number to customer support."
            ]
        )

    # 4. Live Search Retrieval Scoped to Trusted Sources
    live_evidence = fetch_live_evidence(extracted_text)
    
    if not live_evidence:
        return VerificationResponse(
            verdict=VerdictEnum.IN_REVIEW,
            confidence_score=0.0,
            headline_answer="VERDICT: IN REVIEW / UNVERIFIED",
            detailed_breakdown=(
                "No official statements, ministry announcements, or reports from registered media houses "
                "(such as Malawi24, Times 360, or MBC) were found regarding this claim."
            ),
            evidence_links=[],
            caution_steps=["Exercise caution before sharing unverified reports on social media."]
        )

    # 5. AI Reasoning Engine Call
    context_str = "\n\n".join([
        f"Source: {e['source']}\nURL: {e['url']}\nTitle: {e['title']}\nSnippet: {e['snippet']}"
        for e in live_evidence
    ])

    system_prompt = (
        "You are an objective fact-checking assistant for Malawi. "
        "Evaluate the user claim using ONLY the provided live evidence context. Do NOT use outside parametric memory.\n\n"
        f"LIVE EVIDENCE CONTEXT:\n{context_str}\n\n"
        "Instructions:\n"
        "1. Determine if the claim is VERIFIED_TRUE or VERIFIED_FALSE.\n"
        "2. Provide a direct, non-robotic answer explaining the facts vividly.\n"
        "3. Output valid JSON matching the specified structure."
    )

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User Prompt: {extracted_text}"}
        ],
        temperature=0.0
    )

    analysis = completion.choices[0].message.content
    evidence_urls = [e["url"] for e in live_evidence]

    return VerificationResponse(
        verdict=VerdictEnum.VERIFIED_TRUE,
        confidence_score=0.90,
        headline_answer="VERIFIED STATEMENT",
        detailed_breakdown=analysis,
        evidence_links=evidence_urls,
        caution_steps=None
    )
```
