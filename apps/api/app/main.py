import json
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import institutions, screening, sources, stories, verification

app = FastAPI(
    title="VeriFeed API",
    description="API for VeriFeed fact-checking and news platform",
    version="0.2.0",
)

# Configure CORS
origins_str = os.getenv("BACKEND_CORS_ORIGINS", '["http://localhost:3000"]')
try:
    origins_list = json.loads(origins_str)
except json.JSONDecodeError:
    origins_list = ["http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
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

@app.get("/")
def root():
    return {"message": "Welcome to VeriFeed API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
