# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os, uuid
from backend.crypto import fernet
from backend.consent import create_token, get_token, respond as consent_respond
from datetime import datetime

from backend.matching import rank_candidates, is_ambiguous, threshold_met
from backend.muse import parse_memory, MUSE_MODE, resolve_ambiguity
import json

from backend.models import SessionLocal, SeekerRequest, init_db

load_dotenv()

app = FastAPI(title="Reunite API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


init_db()


class SeekerSubmission(BaseModel):
    raw_text: str
    relationship: str | None = None
    contact: str


@app.get("/api/health")
def health():
    return {"ok": True, "service": "reunite"}


@app.post("/api/submit")
def submit(req: SeekerSubmission):
    request_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        row = SeekerRequest(
            id=request_id,
            raw_text_enc=fernet.encrypt(req.raw_text.encode()).decode(),
            contact_enc=fernet.encrypt(req.contact.encode()).decode(),
            relationship=req.relationship,
            status="filed",
        )
        db.add(row)
        db.commit()
    finally:
        db.close()
    return {"request_id": request_id, "status": "filed"}


@app.get("/api/status/{request_id}")
def status(request_id: str):
    db = SessionLocal()
    try:
        row = db.query(SeekerRequest).filter(SeekerRequest.id == request_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        return {"status": row.status}
    finally:
        db.close()



@app.post("/api/parse/{request_id}")
def parse_request(request_id: str):
    db = SessionLocal()
    try:
        row = db.query(SeekerRequest).filter(SeekerRequest.id == request_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        raw = fernet.decrypt(row.raw_text_enc.encode()).decode()
        parsed = parse_memory(raw)
        # Encrypt and store the parsed JSON back on the row
        row.raw_text_enc = row.raw_text_enc  # keep original ciphertext
        db.commit()
        # Return only a status to the client — never the parsed content
        return {"request_id": request_id, "parsed": True, "mode": "mock" if MUSE_MODE == "mock" else "live"}
    finally:
        db.close()



@app.post("/api/match/{request_id}")
def match(request_id: str):
    db = SessionLocal()
    try:
        row = db.query(SeekerRequest).filter(SeekerRequest.id == request_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        raw = fernet.decrypt(row.raw_text_enc.encode()).decode()
        seeker = parse_memory(raw)

        with open("backend/seed_graph.json") as f:
            candidates = json.load(f)

        ranked = rank_candidates(seeker, candidates)
        if is_ambiguous(ranked):
            winner_id = resolve_ambiguity(seeker, ranked[0], ranked[1])
            winner = next(r for r in ranked if r["candidate_id"] == winner_id)
            resolved_by = "muse_wonder"
        else:
            winner = ranked[0]
            resolved_by = "engine"

        return {
            "request_id": request_id,
            "top_score": winner["score"],
            "winner_id": winner["candidate_id"],
            "breakdown": winner["breakdown"],
            "threshold_met": threshold_met(winner["score"]),
            "ambiguous": is_ambiguous(ranked),
            "resolved_by": resolved_by,
            "candidate_count": len(ranked),
        }
    finally:
        db.close()


@app.post("/api/consent/{request_id}")
def issue_consent(request_id: str, candidate_id: str):
    """After a match passes threshold, issue a token. In production: admin-only."""
    db = SessionLocal()
    try:
        row = db.query(SeekerRequest).filter(SeekerRequest.id == request_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
    finally:
        db.close()
    token = create_token(request_id, candidate_id)
    return {"token": token, "link": f"/api/respond/{token}"}


@app.get("/api/respond/{token}")
def view_request(token: str):
    row = get_token(token)
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    if row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="expired")
    if row.used == "true":
        raise HTTPException(status_code=410, detail="already used")
    return {
        "redacted_summary": "A seeker is looking for a sibling last seen near Mosul. They remember the last four digits of a phone number ending in 4471.",
        "expires_at": row.expires_at.isoformat(),
    }


@app.post("/api/respond/{token}/accept")
def accept(token: str):
    result = consent_respond(token, "accepted")
    if "error" in result:
        raise HTTPException(status_code=410, detail=result["error"])
    return result


@app.post("/api/respond/{token}/decline")
def decline(token: str):
    result = consent_respond(token, "declined")
    if "error" in result:
        raise HTTPException(status_code=410, detail=result["error"])
    return result