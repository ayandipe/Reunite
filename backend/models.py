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
    request_id = Column(String, nullable=True)
    candidate_id = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=False)
    used = Column(String, default="false")         # "false" | "true"
    response = Column(String, default="pending")   # pending | accepted | declined
    responded_at = Column(DateTime, nullable=True)
    attempts = Column(Integer, default=0)          # wrong challenge answers
    challenge_answer_enc = Column(String, nullable=True)  # Fernet ciphertext (individual only; NULL for group)
    verified = Column(Boolean, default=False)      # challenge passed
    group_request_id = Column(String, nullable=True)  # set for group tokens
    slot_index = Column(Integer, nullable=True)       # face-slot index for group tokens
    recent_photo_path = Column(String, nullable=True)  # SAM-redacted recent photo in uploads/redacted/


class GroupRequest(Base):
    __tablename__ = "group_requests"

    id = Column(String, primary_key=True)              # UUID
    created_at = Column(DateTime, default=datetime.utcnow)
    raw_text_enc = Column(String, nullable=False)      # Fernet ciphertext
    context_enc = Column(String, nullable=False)       # Fernet ciphertext
    photo_path = Column(String, nullable=True)         # uploads/original/, never served; NULL in names_only mode
    names_json_enc = Column(String, nullable=False)    # Fernet ciphertext of JSON name list
    quiz_json_enc = Column(String, nullable=False)     # Fernet ciphertext of exactly 5 {q, a} objects
    phone_suffix_enc = Column(String, nullable=True)   # Fernet ciphertext, optional
    birth_year = Column(Integer, nullable=True)        # plaintext class year, not PII
    contact_enc = Column(String, nullable=True)        # Fernet ciphertext, optional
    status = Column(String, default="filed")           # filed | matched | partial | complete | expired

def init_db():
    Base.metadata.create_all(bind=engine)
