# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os, uuid

load_dotenv()

app = FastAPI(title="Reunite API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

fernet = Fernet(os.environ["FERNET_KEY"])

class SeekerRequest(BaseModel):
    raw_text: str
    relationship: str | None = None
    contact: str

@app.get("/api/health")
def health():
    return {"ok": True, "service": "reunite"}

@app.post("/api/submit")
def submit(req: SeekerRequest):
    request_id = str(uuid.uuid4())
    encrypted_text = fernet.encrypt(req.raw_text.encode()).decode()
    encrypted_contact = fernet.encrypt(req.contact.encode()).decode()
    return {"request_id": request_id, "status": "filed"}