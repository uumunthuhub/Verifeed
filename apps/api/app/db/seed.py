"""
Seed script: Populate the database with well-known news RSS feeds.
Run with: uv run python -m app.db.seed
"""
import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Any

from app.db.session import SessionLocal
from app.models.source import Source


def source_payload(source: dict[str, Any]) -> dict[str, Any]:
    payload = dict(source)
    hostname = urlparse(str(payload["website_url"])).hostname
    payload["allowed_domains"] = [hostname] if hostname else []
    payload["ingestion_method"] = "rss"
    payload["refresh_minutes"] = 15 if int(str(payload["trust_tier"])) == 1 else 30
    payload["is_active"] = False
    return payload

SOURCES = [
    {"name": "Malawi Government", "website_url": "https://www.malawi.gov.mw/", "rss_url": None, "trust_tier": 1},
    {"name": "Airtel Malawi", "website_url": "https://www.airtel.mw", "rss_url": None, "trust_tier": 1},
    {"name": "TNM Malawi", "website_url": "https://www.tnm.co.mw", "rss_url": None, "trust_tier": 1},

    # Global & World News (Tier 2 - Licensed Media)
    {"name": "BBC World News",     "website_url": "https://www.bbc.com",             "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml", "trust_tier": 2},
    {"name": "BBC Top Stories",    "website_url": "https://www.bbc.com",             "rss_url": "https://feeds.bbci.co.uk/news/rss.xml", "trust_tier": 2},
    {"name": "Reuters News",       "website_url": "https://www.reuters.com",         "rss_url": "https://feeds.reuters.com/reuters/topNews", "trust_tier": 2},
    {"name": "AP News Top",        "website_url": "https://apnews.com",              "rss_url": "https://rsshub.app/apnews/topics/apf-topnews", "trust_tier": 2},
    {"name": "NPR Top News",       "website_url": "https://www.npr.org",             "rss_url": "https://feeds.npr.org/1001/rss.xml", "trust_tier": 2},
    {"name": "The Guardian World", "website_url": "https://www.theguardian.com",     "rss_url": "https://www.theguardian.com/world/rss", "trust_tier": 2},
    {"name": "Al Jazeera English", "website_url": "https://www.aljazeera.com",       "rss_url": "https://www.aljazeera.com/xml/rss/all.xml", "trust_tier": 2},
    {"name": "Deutsche Welle (DW)","website_url": "https://www.dw.com",              "rss_url": "https://rss.dw.com/rdf/rss-en-all", "trust_tier": 2},
    {"name": "France 24",          "website_url": "https://www.france24.com",        "rss_url": "https://www.france24.com/en/rss", "trust_tier": 2},

    # Regional & Africa News (Tier 2)
    {"name": "AllAfrica News",     "website_url": "https://allafrica.com",           "rss_url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "trust_tier": 2},
    {"name": "BBC Africa",         "website_url": "https://www.bbc.com/news/world/africa", "rss_url": "https://feeds.bbci.co.uk/news/world/africa/rss.xml", "trust_tier": 2},
    {"name": "Africanews",         "website_url": "https://www.africanews.com",      "rss_url": "https://www.africanews.com/feed/", "trust_tier": 2},
    {"name": "Times LIVE (ZA)",    "website_url": "https://www.timeslive.co.za",     "rss_url": "https://www.timeslive.co.za/rss/", "trust_tier": 2},

    # Malawi News & Media (Tier 2)
    {"name": "Nyasa Times (MW)",   "website_url": "https://www.nyasatimes.com",      "rss_url": "https://www.nyasatimes.com/feed/", "trust_tier": 2},
    {"name": "Malawi24",           "website_url": "https://malawi24.com",            "rss_url": "https://malawi24.com/feed/", "trust_tier": 2},
    {"name": "The Nation Online",  "website_url": "https://mwnation.com",            "rss_url": "https://mwnation.com/feed/", "trust_tier": 2},
    {"name": "Zodiak Online",      "website_url": "https://www.zodiakmalawi.com/",    "rss_url": "https://www.zodiakmalawi.com/feed/", "trust_tier": 2},
    {"name": "Times TV",           "website_url": "https://times.mw/etimes/",         "rss_url": "https://times.mw/etimes/feed/", "trust_tier": 2},
    {"name": "Luntha TV",          "website_url": "https://lunthatv.com/",            "rss_url": "https://lunthatv.com/feed/", "trust_tier": 2},
    {"name": "MBC Digital",        "website_url": "https://www.mbc.mw",              "rss_url": "https://www.mbc.mw/feed/", "trust_tier": 2},
    {"name": "Malawi Voice",       "website_url": "https://www.malawivoice.com",     "rss_url": "https://www.malawivoice.com/feed/", "trust_tier": 3},
    {"name": "MIJ Online",         "website_url": "https://www.mijmalawi.com",       "rss_url": "https://www.mijmalawi.com/feed/", "trust_tier": 2},

    # Malawi Institutions & Government (Tier 1 — Highest Authority)
    {"name": "MACRA",              "website_url": "https://www.macra.mw",            "rss_url": "https://www.macra.mw/feed/", "trust_tier": 1},
    {"name": "Reserve Bank of Malawi", "website_url": "https://www.rbm.mw",         "rss_url": "https://www.rbm.mw/feed/", "trust_tier": 1},
    {"name": "Malawi Stock Exchange",  "website_url": "https://www.mse.co.mw",      "rss_url": "https://www.mse.co.mw/feed/", "trust_tier": 1},
    {"name": "Malawi Revenue Authority", "website_url": "https://www.mra.mw",       "rss_url": "https://www.mra.mw/feed/", "trust_tier": 1},

    # Business & Economy (Tier 2)
    {"name": "Financial Times",    "website_url": "https://www.ft.com",              "rss_url": "https://www.ft.com/rss/home", "trust_tier": 2},
    {"name": "CNBC Business",      "website_url": "https://www.cnbc.com",            "rss_url": "https://search.cnbc.com/rs/search/combinedrenderer.view?query=news&partnerId=2000&target=news", "trust_tier": 2},
    {"name": "MarketWatch Top",    "website_url": "https://www.marketwatch.com",     "rss_url": "https://feeds.content.dowjones.io/public/rss/mw_topstories", "trust_tier": 2},

    # Technology (Tier 2/3)
    {"name": "TechCrunch",         "website_url": "https://techcrunch.com",          "rss_url": "https://techcrunch.com/feed/", "trust_tier": 2},
    {"name": "The Verge",          "website_url": "https://www.theverge.com",        "rss_url": "https://www.theverge.com/rss/index.xml", "trust_tier": 2},
    {"name": "Ars Technica",       "website_url": "https://arstechnica.com",         "rss_url": "https://feeds.arstechnica.com/arstechnica/index", "trust_tier": 2},
    {"name": "Wired Top",          "website_url": "https://www.wired.com",           "rss_url": "https://www.wired.com/feed/rss", "trust_tier": 2},

    # Health & Science (Tier 2)
    {"name": "Science Daily",      "website_url": "https://www.sciencedaily.com",    "rss_url": "https://www.sciencedaily.com/rss/top/science.xml", "trust_tier": 2},
    {"name": "Nature News",        "website_url": "https://www.nature.com",          "rss_url": "https://www.nature.com/nature.rss", "trust_tier": 1},
    {"name": "Medical News Today", "website_url": "https://www.medicalnewstoday.com", "rss_url": "https://rss.medicalnewstoday.com/featurednews.xml", "trust_tier": 2},

    # Sports (Tier 3)
    {"name": "ESPN Top News",      "website_url": "https://www.espn.com",            "rss_url": "https://www.espn.com/espn/rss/news", "trust_tier": 3},
    {"name": "BBC Sport",          "website_url": "https://www.bbc.com/sport",       "rss_url": "https://feeds.bbci.co.uk/sport/rss.xml", "trust_tier": 3},

    # Politics (Tier 2)
    {"name": "Politico Top Picks", "website_url": "https://www.politico.com",        "rss_url": "https://www.politico.com/rss/politicopicks.xml", "trust_tier": 2},
    {"name": "The Hill News",      "website_url": "https://thehill.com",             "rss_url": "https://thehill.com/feed/", "trust_tier": 2},
]

def seed():
    db = SessionLocal()
    try:
        added = 0
        updated = 0
        for source in SOURCES:
            src = source_payload(source)
            existing = db.query(Source).filter(Source.name == src["name"]).first()
            if not existing:
                db.add(Source(**src))
                added += 1
            else:
                fields = ("rss_url", "trust_tier", "allowed_domains", "ingestion_method", "refresh_minutes", "is_active")
                if any(getattr(existing, field) != src[field] for field in fields):
                    for field in fields:
                        setattr(existing, field, src[field])
                    updated += 1
        db.commit()
        print(f"✅ Seeded {added} new sources, updated {updated} existing sources. Total: {len(SOURCES)} sources.")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
