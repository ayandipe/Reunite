# backend/consent.py
import secrets, uuid
from datetime import datetime, timedelta
from backend.models import SessionLocal, ConsentToken, SeekerRequest
from backend.crypto import fernet  # we'll move fernet here next

TOKEN_TTL_HOURS = 24


def create_token(request_id: str, candidate_id: str) -> str:
    db = SessionLocal()
    try:
        token = secrets.token_urlsafe(32)
        row = ConsentToken(
            id=str(uuid.uuid4()),
            match_id="pending",
            token=token,
            request_id=request_id,
            candidate_id=candidate_id,
            expires_at=datetime.utcnow() + timedelta(hours=TOKEN_TTL_HOURS),
            used="false",
            response="pending",
        )
        db.add(row)
        db.commit()
        return token
    finally:
        db.close()


def get_token(token: str) -> ConsentToken | None:
    db = SessionLocal()
    try:
        return db.query(ConsentToken).filter(ConsentToken.token == token).first()
    finally:
        db.close()


def respond(token: str, decision: str) -> dict:
    """decision: 'accepted' or 'declined'. Returns status for the recipient only."""
    db = SessionLocal()
    try:
        row = db.query(ConsentToken).filter(ConsentToken.token == token).first()
        if not row:
            return {"error": "not_found"}
        if row.used == "true":
            return {"error": "already_used"}
        if row.expires_at < datetime.utcnow():
            return {"error": "expired"}

        row.used = "true"
        row.response = decision
        row.responded_at = datetime.utcnow()

        if decision == "accepted":
            # Only on acceptance does the seeker's request move forward
            req = db.query(SeekerRequest).filter(SeekerRequest.id == row.request_id).first()
            if req:
                req.status = "accepted"

        db.commit()

        # SILENT DECLINE: if decision == "declined", we intentionally
        # do NOT touch the seeker's request. Its status stays 'filed'.
        return {"status": "closed"}
    finally:
        db.close()