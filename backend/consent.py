# backend/consent.py
import secrets, uuid
from datetime import datetime, timedelta
from backend.models import SessionLocal, ConsentToken, SeekerRequest
from backend.crypto import fernet  # we'll move fernet here next
from backend.muse import parse_memory

TOKEN_TTL_HOURS = 24
MAX_ATTEMPTS = 3


def _challenge_answer(request_id: str) -> str | None:
    """Last two digits of the seeker's remembered phone suffix, if any."""
    db = SessionLocal()
    try:
        req = db.query(SeekerRequest).filter(SeekerRequest.id == request_id).first()
        if not req:
            return None
        raw = fernet.decrypt(req.raw_text_enc.encode()).decode()
        suffix = parse_memory(raw).get("phone_suffix")
        if not suffix or len(suffix) < 2:
            return None
        return suffix[-2:]
    finally:
        db.close()


def create_token(request_id: str, candidate_id: str) -> str:
    db = SessionLocal()
    try:
        answer = _challenge_answer(request_id)
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
            challenge_answer_enc=fernet.encrypt(answer.encode()).decode() if answer else None,
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


def verify_answer(token: str, answer: str) -> dict:
    """Check the challenge answer. Never consumes the token on its own."""
    db = SessionLocal()
    try:
        row = db.query(ConsentToken).filter(ConsentToken.token == token).first()
        if not row:
            return {"error": "not_found"}
        if row.expires_at < datetime.utcnow():
            return {"error": "expired"}
        if row.used == "true":
            return {"error": "already_used"}
        if (row.attempts or 0) >= MAX_ATTEMPTS:
            close = True
        else:
            expected = (
                fernet.decrypt(row.challenge_answer_enc.encode()).decode()
                if row.challenge_answer_enc
                else None
            )
            if expected is None or (answer or "").strip() == expected:
                row.verified = True
                db.commit()
                return {"verified": True}
            row.attempts = (row.attempts or 0) + 1
            db.commit()
            close = row.attempts >= MAX_ATTEMPTS
    finally:
        db.close()
    if close:
        # Third strike: silent decline. The seeker's status stays 'filed'.
        respond(token, "declined")
        return {"error": "locked"}
    return {"error": "incorrect"}


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