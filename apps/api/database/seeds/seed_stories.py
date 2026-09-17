import datetime
import logging
from typing import TypedDict

from app.db.session import SessionLocal
from app.models.article import Article
from app.models.source import Source
from app.models.story import Story
from app.services.ingestion import categorize_headline

logger = logging.getLogger(__name__)


class SourceSeed(TypedDict):
    name: str
    website_url: str
    rss_url: str


class ArticleSeed(TypedDict):
    source_name: str
    headline: str
    url: str
    content: str


class StorySeed(TypedDict):
    category: str
    title: str
    summary: str
    articles: list[ArticleSeed]


INITIAL_SOURCES: list[SourceSeed] = [
    {"name": "Zodiak TV", "website_url": "https://zodiakmalawi.com", "rss_url": "https://zodiakmalawi.com/feed/tv"},
    {"name": "Zodiak Online", "website_url": "https://zodiakmalawi.com", "rss_url": "https://zodiakmalawi.com/feed"},
    {"name": "Times 360 Malawi", "website_url": "https://times.mw", "rss_url": "https://times.mw/feed"},
    {"name": "BBC News", "website_url": "https://bbc.com/news", "rss_url": "https://feeds.bbci.co.uk/news/rss.xml"},
    {"name": "Reuters", "website_url": "https://reuters.com", "rss_url": "https://feeds.reuters.com/reuters/topNews"},
    {"name": "AP News", "website_url": "https://apnews.com", "rss_url": "https://rsshub.app/apnews/topics/apf-topnews"},
    {"name": "The Guardian", "website_url": "https://theguardian.com", "rss_url": "https://www.theguardian.com/world/rss"},
    {"name": "Al Jazeera", "website_url": "https://aljazeera.com", "rss_url": "https://www.aljazeera.com/xml/rss/all.xml"},
    {"name": "TechCrunch", "website_url": "https://techcrunch.com", "rss_url": "https://techcrunch.com/feed/"},
]

SEED_STORIES: list[StorySeed] = [
    {
        "category": "Politics",
        "title": "Parliament Approves National Digital Verification Infrastructure Bill",
        "summary": "Lawmakers vote unanimously to establish public threat verification centers and digital security frameworks.",
        "articles": [
            {
                "source_name": "Zodiak TV",
                "headline": "Zodiak TV Report: Parliament Passes Key Digital Integrity & Cybersecurity Bill",
                "url": "https://zodiakmalawi.com/news/malawi-parliament-cyber-bill-2026",
                "content": "Members of Parliament passed sweeping legislation establishing public threat verification centers and digital security frameworks."
            },
            {
                "source_name": "Zodiak Online",
                "headline": "Zodiak Online: Combatting SMS Impersonation Fraud Across Districts",
                "url": "https://zodiakmalawi.com/news/zodiak-online-report-sms-fraud",
                "content": "Zodiak TV investigates the rising trend of mobile money SMS fraud targeting rural consumers."
            }
        ]
    },
    {
        "category": "Politics",
        "title": "Global Leaders Convene for Summit on Misinformation Governance",
        "summary": "Representatives from 40 nations agreed on new transparent standards for digital content provenance and AI-generated media regulation.",
        "articles": [
            {
                "source_name": "BBC News",
                "headline": "Global Leaders Convene for Summit on Misinformation Governance",
                "url": "https://bbc.com/news/world-politics-6819201",
                "content": "Ministers and technology leaders gathered in Geneva to establish shared standards for verification and content authenticity."
            },
            {
                "source_name": "Reuters",
                "headline": "Geneva Accord Sets New Standards for AI Media Labelling",
                "url": "https://reuters.com/world/geneva-ai-summit-accord-2026",
                "content": "The multilateral treaty requires major platforms to embed verifiable cryptographic signatures in generated images and audio."
            }
        ]
    },
    {
        "category": "Politics",
        "title": "Parliament Debates Bipartisan Electoral Integrity Legislation",
        "summary": "Lawmakers introduce strict penalties for deepfake audio campaigns targeting political candidates within 30 days of elections.",
        "articles": [
            {
                "source_name": "The Guardian",
                "headline": "Bipartisan Coalition Introduces Deepfake Election Protection Act",
                "url": "https://theguardian.com/politics/deepfake-election-bill-2026",
                "content": "The proposed bill mandates rapid removal of synthetic voice impersonations during election periods."
            }
        ]
    },
    {
        "category": "Health",
        "title": "WHO Issues Guidance on Medical Social Media Scams & Fake Cure Claims",
        "summary": "Health officials warn against fraudulent online sellers offering unverified miracle treatments for chronic conditions.",
        "articles": [
            {
                "source_name": "AP News",
                "headline": "WHO Warns Against Online Fraudulent Remedy Schemes",
                "url": "https://apnews.com/health/who-fake-cure-warning-2026",
                "content": "The World Health Organization published an alert regarding synthetic ad campaigns impersonating prominent medical doctors."
            },
            {
                "source_name": "BBC News",
                "headline": "Regulators Target Social Media Accounts Promoting Fake Miracle Drugs",
                "url": "https://bbc.com/news/health-6819299",
                "content": "Health regulators have requested swift removal of unauthorized supplement advertisements using forged hospital branding."
            }
        ]
    },
    {
        "category": "Technology",
        "title": "AI Detection Systems Reach 98% Precision on Voice Impersonations",
        "summary": "Researchers demonstrate acoustic spectral analysis algorithms capable of flagging cloned voice phishing calls in under 50 milliseconds.",
        "articles": [
            {
                "source_name": "TechCrunch",
                "headline": "Real-Time Voice Phishing Defense Benchmark Released",
                "url": "https://techcrunch.com/2026/09/15/voice-phishing-defense-ai/",
                "content": "New lightweight neural models enable on-device call screening without sending private voice streams to remote cloud servers."
            }
        ]
    },
    {
        "category": "Business",
        "title": "Central Banks Alert Consumers to Synthetic Banking Phishing Portals",
        "summary": "Financial regulators report a surge in fraudulent SMS messages linking to pixel-perfect replicas of major retail banking login screens.",
        "articles": [
            {
                "source_name": "Reuters",
                "headline": "Banking Regulators Issue Urgent Warning Over SMS Login Spoofing",
                "url": "https://reuters.com/business/finance/banking-sms-phishing-alert-2026",
                "content": "Consumers are urged to verify incoming SMS links against official bank domains before entering authentication credentials."
            }
        ]
    },
    {
        "category": "World",
        "title": "International Cybersecurity Coalition Neutralizes Global Smishing Ring",
        "summary": "Law enforcement agencies across three continents dismantle a criminal network responsible for millions of automated parcel tracking scams.",
        "articles": [
            {
                "source_name": "Al Jazeera",
                "headline": "Global Operation Shuts Down Automated SMS Fraud Infrastructure",
                "url": "https://aljazeera.com/news/2026/09/16/global-sms-fraud-ring-dismantled",
                "content": "Coordination between Europol, Interpol, and national telcos led to the seizure of over 400 SIM farm gateways."
            }
        ]
    },
    {
        "category": "Regional",
        "title": "Regional Digital Literacy Drive Launches Across SADC Nations",
        "summary": "Educational initiatives launch in Southern Africa to equip citizens with digital verification tools against SMS lottery and job scam lures.",
        "articles": [
            {
                "source_name": "Al Jazeera",
                "headline": "SADC Community Programs Empower Citizens Against Mobile Fraud",
                "url": "https://aljazeera.com/news/2026/09/10/sadc-digital-literacy-fraud",
                "content": "Community workshops and mobile screening apps help local residents identify impersonation scams and fake emergency wire requests."
            }
        ]
    },
    {
        "category": "Sports",
        "title": "Major League Security Panel Warns Fans Against Unofficial Ticket Portals",
        "summary": "Championship event organizers warn spectators about counterfeit ticketing websites operating fake domain names.",
        "articles": [
            {
                "source_name": "BBC News",
                "headline": "Fans Warned of Fraudulent Ticket Resale Sites for Finals",
                "url": "https://bbc.com/sport/6819400",
                "content": "Official organizers remind supporters to purchase tickets exclusively through authenticated partner channels."
            }
        ]
    },
    {
        "category": "Entertainment",
        "title": "Cybersecurity Watchdog Flags Deepfake Celebrity Endorsement Network",
        "summary": "Ad networks remove thousands of unauthorized synthetic videos using celebrity likenesses to promote cryptocurrency scams.",
        "articles": [
            {
                "source_name": "The Guardian",
                "headline": "Celebrity Impersonation Ads Pulled from Social Video Platforms",
                "url": "https://theguardian.com/technology/celebrity-deepfake-ads-pulled",
                "content": "Automated ad moderation tools flagged coordinated networks broadcasting fake celebrity investment endorsements."
            }
        ]
    }
]

def seed_news_data():
    db = SessionLocal()
    try:
        # 1. Ensure sources exist
        source_map = {}
        for s_data in INITIAL_SOURCES:
            source = db.query(Source).filter(Source.name == s_data["name"]).first()
            if not source:
                source = Source(
                    name=s_data["name"],
                    website_url=s_data["website_url"],
                    rss_url=s_data["rss_url"]
                )
                db.add(source)
                db.commit()
                db.refresh(source)
            source_map[source.name] = source

        # 2. Seed stories and articles
        stories_created = 0
        articles_created = 0

        for story_data in SEED_STORIES:
            existing_story = db.query(Story).filter(Story.title == story_data["title"]).first()
            if not existing_story:
                story = Story(
                    title=story_data["title"],
                    category=story_data["category"],
                    summary=story_data["summary"],
                    created_at=datetime.datetime.now(datetime.timezone.utc)
                )
                db.add(story)
                db.commit()
                db.refresh(story)
                stories_created += 1
            else:
                story = existing_story

            for a_data in story_data["articles"]:
                source = source_map.get(a_data["source_name"])
                if not source:
                    continue
                existing_article = db.query(Article).filter(Article.url == a_data["url"]).first()
                if not existing_article:
                    article = Article(
                        source_id=source.id,
                        story_id=story.id,
                        headline=a_data["headline"],
                        url=a_data["url"],
                        content=a_data["content"],
                        published_at=datetime.datetime.now(datetime.timezone.utc)
                    )
                    db.add(article)
                    articles_created += 1

        db.commit()
        print(f"✅ Seeding complete! Created {stories_created} new stories and {articles_created} new articles.")

    except Exception as e:
        db.rollback()
        print(f"❌ Error seeding news data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    seed_news_data()
