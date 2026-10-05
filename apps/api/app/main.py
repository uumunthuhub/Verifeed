import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import facebook_webhook, institutions, screening, sources, stories, verification, whatsapp_webhook

app = FastAPI(
    title="VeriFeed API",
    description="API for VeriFeed fact-checking and news platform",
    version="0.2.0",
)

# Configure CORS
DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
origins_str = os.getenv("BACKEND_CORS_ORIGINS", "")
if origins_str:
    try:
        origins_list = json.loads(origins_str)
    except json.JSONDecodeError:
        origins_list = DEFAULT_ORIGINS
else:
    origins_list = DEFAULT_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(stories.router, prefix="/api/v1/stories", tags=["stories"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(verification.router, prefix="/api/v1/verify", tags=["verification"])
app.include_router(screening.router, prefix="/api/v1/screen", tags=["screening"])
app.include_router(institutions.router, prefix="/api/v1/institutions", tags=["institutions"])
app.include_router(facebook_webhook.router, prefix="/api/v1/facebook", tags=["facebook"])
app.include_router(whatsapp_webhook.router, prefix="/api/v1/whatsapp", tags=["whatsapp"])

@app.get("/")
def root():
    return {"message": "Welcome to VeriFeed API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/privacy")
def privacy_policy_info():
    return {
        "title": "VeriFeed Privacy Policy",
        "policy_url": "https://verifeed.org/privacy",
        "meta_data_deletion_url": "https://verifeed.org/privacy#data-deletion",
        "contact_email": "privacy@verifeed.org",
        "effective_date": "2026-10-03",
        "compliance": ["Meta Developer Policy", "GDPR", "On-Device Privacy First"],
    }

@app.get("/data-deletion")
def data_deletion_instructions():
    return {
        "service": "VeriFeed Meta Data Deletion Instructions",
        "instructions": "To request deletion of Facebook data, email privacy@verifeed.org with your Facebook Page ID or remove the VeriFeed App under Facebook Settings > Apps and Websites.",
        "deletion_url": "https://verifeed.org/privacy#data-deletion",
        "response_time": "48 hours",
    }

