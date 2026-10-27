# backend/main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os, uuid

from backend.models import SessionLocal, SeekerRequest, init_db

load_dotenv()

app = FastAPI(title="Reunite API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

fernet = Fernet(os.environ["FERNET_KEY"])
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