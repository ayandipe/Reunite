# backend/models.py
from sqlalchemy import Boolean, Column, Integer, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os
import pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/backend/reunite.db")


engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class SeekerRequest(Base):
    __tablename__ = "seeker_requests"

    id = Column(String, primary_key=True)              # UUID
    created_at = Column(DateTime, default=datetime.utcnow)
    raw_text_enc = Column(String, nullable=False)      # Fernet ciphertext
    contact_enc = Column(String, nullable=False)       # Fernet ciphertext
    relationship = Column(String, nullable=True)
    status = Column(String, default="filed")           # filed | matched | accepted | declined | expired


class ConsentToken(Base):
    __tablename__ = "consent_tokens"

    id = Column(String, primary_key=True)
    match_id = Column(String, nullable=False)      # placeholder until Match table exists
    token = Column(String, unique=True, nullable=False, index=True)
    request_id = Column(String, nullable=False)
    candidate_id = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(String, default="false")         # "false" | "true"
    response = Column(String, default="pending")   # pending | accepted | declined
    responded_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0)          # wrong challenge answers
    challenge_answer_enc = Column(String, nullable=True)  # Fernet ciphertext
    verified = Column(Boolean, default=False)      # challenge passed

def init_db():
    Base.metadata.create_all(bind=engine)
    _ensure_consent_columns()


def _ensure_consent_columns():
    """Add newer ConsentToken columns to databases created before them."""
    from sqlalchemy import text
    with engine.begin() as conn:
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(consent_tokens)"))}
        if "attempts" not in existing:
            conn.execute(text("ALTER TABLE consent_tokens ADD COLUMN attempts INTEGER DEFAULT 0"))
        if "challenge_answer_enc" not in existing:
            conn.execute(text("ALTER TABLE consent_tokens ADD COLUMN challenge_answer_enc VARCHAR"))
        if "verified" not in existing:
            conn.execute(text("ALTER TABLE consent_tokens ADD COLUMN verified BOOLEAN DEFAULT 0"))