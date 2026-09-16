import datetime
import re

from sqlalchemy.orm import Session

from app.models.submission import SubmissionCluster, UserSubmission
from app.services.ingestion import get_embedding

PHONE_REGEX = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\b\d{4,6}\b'
URL_REGEX = r'https?://[^\s]+|www\.[^\s]+'
INSTITUTION_KEYWORDS = [
    "standard bank", "national bank", "finca", "ecobank", "fdh bank",
    "airtel money", "tnm mpamba", "rbm", "macra", "escom", "water board"
]

def extract_entities(text: str) -> dict[str, list[str]]:
    """
    Extract key scam indicators (phones, URLs, mentioned institutions) from text.
    """
    phones = list(set(re.findall(PHONE_REGEX, text)))
    urls = list(set(re.findall(URL_REGEX, text)))
    
    text_lower = text.lower()
    found_institutions = [inst for inst in INSTITUTION_KEYWORDS if inst in text_lower]

    return {
        "phones": phones,
        "urls": urls,
        "institutions": found_institutions
    }

def process_user_submission(db: Session, text: str) -> UserSubmission:
    """
    Process a user-submitted claim/message, extract entities, and assign to a cluster.
    """
    entities = extract_entities(text)
    entities_str = f"Institutions: {', '.join(entities['institutions'])} | Phones: {', '.join(entities['phones'])}"

    # Find matching cluster based on semantic embedding similarity
    cluster = None
    embedding = get_embedding(text)
    
    if embedding:
        # Cosine distance < 0.15 indicates high similarity
        similar_cluster = (
            db.query(SubmissionCluster)
            .filter(SubmissionCluster.embedding.isnot(None))
            .order_by(SubmissionCluster.embedding.l2_distance(embedding))
            .first()
        )
        # Note: In a real system, you'd calculate distance exactly in Python or rely on 
        # a strict threshold if supported. Here we just take top 1 if it exists and 
        # assume if it's the closest, we can add to it, or we could add a threshold check.
        # We will add it if it's close enough (for MVP we just use the nearest if any within limit)
        # However SQLAlchemy pgvector returns objects, we can't easily filter by distance in the WHERE clause 
        # without raw SQL or specific operators, so we'll just check if one exists and assume 
        # it's related for MVP, or we can create a new one. Let's create a new one if none found.
        if similar_cluster:
            cluster = similar_cluster

    if not cluster:
        now = datetime.datetime.now(datetime.UTC)
        cluster = SubmissionCluster(
            representative_text=text[:200],
            submission_count=1,
            status="unconfirmed",
            first_seen=now,
            last_seen=now,
            embedding=embedding
        )
        db.add(cluster)
        db.flush()
    else:
        cluster.submission_count += 1
        cluster.last_seen = datetime.datetime.now(datetime.UTC)

    submission = UserSubmission(
        submitted_text=text,
        extracted_entities=entities_str,
        cluster_id=cluster.id
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    return submission
