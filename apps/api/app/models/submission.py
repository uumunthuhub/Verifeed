import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SubmissionCluster(Base):
    __tablename__ = "submission_clusters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    representative_text: Mapped[str] = mapped_column(Text, nullable=False)
    submission_count: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(50), default="unconfirmed")
    first_seen: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    last_seen: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    embedding: Mapped[Vector | None] = mapped_column(Vector(768), nullable=True)

    submissions = relationship("UserSubmission", back_populates="cluster")


class UserSubmission(Base):
    __tablename__ = "user_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    submitted_text: Mapped[str] = mapped_column(Text, nullable=False)
    extracted_entities: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow)
    cluster_id: Mapped[int | None] = mapped_column(ForeignKey("submission_clusters.id"), nullable=True)

    cluster = relationship("SubmissionCluster", back_populates="submissions")
