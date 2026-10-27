# backend/models.py
from sqlalchemy import Column, String, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./backend/reunite.db")

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


def init_db():
    Base.metadata.create_all(bind=engine)