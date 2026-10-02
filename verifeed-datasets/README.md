# VeriFeed Local Media & Sample Dataset Storage

This directory is the dedicated local storage for media samples (SMS screenshots, promo graphics, forged memos, fake WhatsApp screenshots, and scam audio voice notes).

## Directory Layout

```
verifeed-datasets/
├── reference/                         # LEGITIMATE & OFFICIAL COMMUNICATIONS
│   ├── official_sms_screenshots/      # Screenshots of official TNM / Airtel / Bank SMS
│   ├── official_promos/               # Official promo graphics, leaflets, and press PDFs
│   └── official_audio/                # Official voice announcements and radio spots
│
├── negative/                          # FAKE, FRAUDULENT & SCAM SAMPLE DATASET
│   ├── fake_sms_screenshots/          # Screenshots of fake SMS money transfer requests
│   ├── fake_promos/                   # WhatsApp instant loan flyers, fake giveaways
│   ├── scam_audio/                    # Scam audio voice notes (.mp3, .wav, .m4a)
│   └── phishing_screenshots/          # Screenshots of fake login pages / phishing links
│
├── evaluation/                        # HOLDOUT EVALUATION SET (Used for accuracy tests)
└── manifests/                         # JSONL Index Manifests (reference.jsonl, negative.jsonl)
```

## How to Feed Images and Audio to VeriFeed

1. **Drop your media files** directly into the appropriate folder above (e.g., place a fake SMS screenshot inside `negative/fake_sms_screenshots/fake_sms_01.png` or scam audio inside `negative/scam_audio/voice_note_01.mp3`).

2. **Run the Media Ingestion Script:**
   ```bash
   python apps/api/ingest_media_samples.py
   ```

3. **What VeriFeed does when you ingest media:**
   - **For Images (.png, .jpg):** Runs OCR text extraction + perceptual hash (`pHash`) fingerprinting + Gemini Vision authenticity analysis.
   - **For Audio (.mp3, .wav, .m4a):** Runs Speech-to-Text voice transcription to extract claims, phone numbers, and Chichewa/English keywords.
   - **Database Indexing:** Automatically registers extracted text into `dataset_samples` and `dataset_assets` tables in PostgreSQL.
