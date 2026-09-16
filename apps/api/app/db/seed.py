"""
Seed script: Populate the database with well-known news RSS feeds.
Run with: uv run python -m app.db.seed
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.db.session import SessionLocal
from app.models.source import Source

SOURCES = [
    # Global & World News
    {"name": "BBC World News",     "website_url": "https://www.bbc.com",             "rss_url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
    {"name": "BBC Top Stories",    "website_url": "https://www.bbc.com",             "rss_url": "https://feeds.bbci.co.uk/news/rss.xml"},
    {"name": "Reuters News",       "website_url": "https://www.reuters.com",         "rss_url": "https://feeds.reuters.com/reuters/topNews"},
    {"name": "AP News Top",        "website_url": "https://apnews.com",              "rss_url": "https://rsshub.app/apnews/topics/apf-topnews"},
    {"name": "NPR Top News",       "website_url": "https://www.npr.org",             "rss_url": "https://feeds.npr.org/1001/rss.xml"},
    {"name": "The Guardian World", "website_url": "https://www.theguardian.com",     "rss_url": "https://www.theguardian.com/world/rss"},
    {"name": "Al Jazeera English", "website_url": "https://www.aljazeera.com",       "rss_url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"name": "Deutsche Welle (DW)","website_url": "https://www.dw.com",              "rss_url": "https://rss.dw.com/rdf/rss-en-all"},
    {"name": "France 24",          "website_url": "https://www.france24.com",        "rss_url": "https://www.france24.com/en/rss"},

    # Regional & Africa News
    {"name": "AllAfrica News",     "website_url": "https://allafrica.com",           "rss_url": "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf"},
    {"name": "BBC Africa",         "website_url": "https://www.bbc.com/news/world/africa", "rss_url": "https://feeds.bbci.co.uk/news/world/africa/rss.xml"},
    {"name": "Africanews",         "website_url": "https://www.africanews.com",      "rss_url": "https://www.africanews.com/feed/"},
    {"name": "Times LIVE (ZA)",    "website_url": "https://www.timeslive.co.za",     "rss_url": "https://www.timeslive.co.za/rss/"},

    # Malawi News & Media
    {"name": "Nyasa Times (MW)",   "website_url": "https://www.nyasatimes.com",      "rss_url": "https://www.nyasatimes.com/feed/"},
    {"name": "Malawi24",           "website_url": "https://malawi24.com",            "rss_url": "https://malawi24.com/feed/"},
    {"name": "The Nation Online",  "website_url": "https://mwnation.com",            "rss_url": "https://mwnation.com/feed/"},
    {"name": "Zodiak Online",      "website_url": "https://www.zodiakmalawi.com",    "rss_url": "https://www.zodiakmalawi.com/feed/"},
    {"name": "MBC Digital",        "website_url": "https://www.mbc.mw",              "rss_url": "https://www.mbc.mw/feed/"},
    {"name": "Malawi Voice",       "website_url": "https://www.malawivoice.com",     "rss_url": "https://www.malawivoice.com/feed/"},
    {"name": "MIJ Online",         "website_url": "https://www.mijmalawi.com",       "rss_url": "https://www.mijmalawi.com/feed/"},

    # Malawi Institutions & Government
    {"name": "MACRA",              "website_url": "https://www.macra.mw",            "rss_url": "https://www.macra.mw/feed/"},
    {"name": "Reserve Bank of Malawi", "website_url": "https://www.rbm.mw",         "rss_url": "https://www.rbm.mw/feed/"},
    {"name": "Malawi Stock Exchange",  "website_url": "https://www.mse.co.mw",      "rss_url": "https://www.mse.co.mw/feed/"},
    {"name": "Malawi Revenue Authority", "website_url": "https://www.mra.mw",       "rss_url": "https://www.mra.mw/feed/"},

    # Business & Economy
    {"name": "Financial Times",    "website_url": "https://www.ft.com",              "rss_url": "https://www.ft.com/rss/home"},
    {"name": "CNBC Business",      "website_url": "https://www.cnbc.com",            "rss_url": "https://search.cnbc.com/rs/search/combinedrenderer.view?query=news&partnerId=2000&target=news"},
    {"name": "MarketWatch Top",    "website_url": "https://www.marketwatch.com",     "rss_url": "https://feeds.content.dowjones.io/public/rss/mw_topstories"},

    # Technology
    {"name": "TechCrunch",         "website_url": "https://techcrunch.com",          "rss_url": "https://techcrunch.com/feed/"},
    {"name": "The Verge",          "website_url": "https://www.theverge.com",        "rss_url": "https://www.theverge.com/rss/index.xml"},
    {"name": "Ars Technica",       "website_url": "https://arstechnica.com",         "rss_url": "https://feeds.arstechnica.com/arstechnica/index"},
    {"name": "Wired Top",          "website_url": "https://www.wired.com",           "rss_url": "https://www.wired.com/feed/rss"},

    # Health & Science
    {"name": "Science Daily",      "website_url": "https://www.sciencedaily.com",    "rss_url": "https://www.sciencedaily.com/rss/top/science.xml"},
    {"name": "Nature News",        "website_url": "https://www.nature.com",          "rss_url": "https://www.nature.com/nature.rss"},
    {"name": "Medical News Today", "website_url": "https://www.medicalnewstoday.com", "rss_url": "https://rss.medicalnewstoday.com/featurednews.xml"},

    # Sports
    {"name": "ESPN Top News",      "website_url": "https://www.espn.com",            "rss_url": "https://www.espn.com/espn/rss/news"},
    {"name": "BBC Sport",          "website_url": "https://www.bbc.com/sport",       "rss_url": "https://feeds.bbci.co.uk/sport/rss.xml"},

    # Politics
    {"name": "Politico Top Picks", "website_url": "https://www.politico.com",        "rss_url": "https://www.politico.com/rss/politicopicks.xml"},
    {"name": "The Hill News",      "website_url": "https://thehill.com",             "rss_url": "https://thehill.com/feed/"},
]


def seed():
    db = SessionLocal()
    try:
        added = 0
        for src in SOURCES:
            existing = db.query(Source).filter(Source.name == src["name"]).first()
            if not existing:
                db.add(Source(**src))
                added += 1
        db.commit()
        print(f"✅ Seeded {added} new sources ({len(SOURCES) - added} already existed). Total: {len(SOURCES)} sources.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()

