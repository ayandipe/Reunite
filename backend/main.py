# backend/main.py
from fastapi import UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from backend.sam import redact_image
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os, secrets, uuid
from backend.crypto import fernet
from backend.consent import (
    create_token,
    get_token,
    respond as consent_respond,
    verify_answer as consent_verify_answer,
)
from datetime import datetime, timedelta

from backend.matching import rank_candidates, is_ambiguous, threshold_met
from backend.muse import parse_memory, MUSE_MODE, resolve_ambiguity
import json

from backend.models import SessionLocal, SeekerRequest, GroupRequest, ConsentToken, init_db
from backend.sam import UPLOAD_REDACTED, UPLOAD_ORIG

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
            "ranked": ranked,
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
    if getattr(row, "group_request_id", None):
        db = SessionLocal()
        try:
            group = db.query(GroupRequest).filter(GroupRequest.id == row.group_request_id).first()
            if not group:
                raise HTTPException(status_code=404, detail="not found")
            context = fernet.decrypt(group.context_enc.encode()).decode()
            names = json.loads(fernet.decrypt(group.names_json_enc.encode()).decode())
            name = names[row.slot_index] if row.slot_index is not None and 0 <= row.slot_index < len(names) else None
            quiz = json.loads(fernet.decrypt(group.quiz_json_enc.encode()).decode())
            questions = [item["q"] for item in quiz]
        finally:
            db.close()
        return {
            "redacted_summary": (
                f"A former classmate is looking for people from {context}. "
                f"You appear to be {name} in a group photo they filed."
            ),
            "quiz": questions,
            "pass_threshold": 4,
            "expires_at": row.expires_at.isoformat(),
        }
    return {
        "redacted_summary": "A seeker is looking for a sibling last seen near Mosul. They remember the last four digits of a phone number ending in 4471.",
        "expires_at": row.expires_at.isoformat(),
    }


class VerifyAnswer(BaseModel):
    answer: str | None = None
    answers: list[str] | None = None


QUIZ_PASS_THRESHOLD = 4


def _verify_group_quiz(token: str, answers: list[str] | None) -> dict:
    """4-of-5 quiz path for group tokens. Returns a result dict or raises HTTPException."""
    db = SessionLocal()
    try:
        row = db.query(ConsentToken).filter(ConsentToken.token == token).first()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        if row.expires_at < datetime.utcnow():
            raise HTTPException(status_code=410, detail="expired")
        if row.used == "true":
            raise HTTPException(status_code=410, detail="already used")
        group = db.query(GroupRequest).filter(GroupRequest.id == row.group_request_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="not found")
        quiz = json.loads(fernet.decrypt(group.quiz_json_enc.encode()).decode())
        given = answers or []
        correct = sum(
            1 for i, item in enumerate(quiz)
            if i < len(given) and (given[i] or "").strip().lower() == (item["a"] or "").strip().lower()
        )
        if correct >= QUIZ_PASS_THRESHOLD:
            row.verified = True
            db.commit()
            return {"verified": True, "correct": correct, "required": QUIZ_PASS_THRESHOLD}
        if (row.attempts or 0) >= 1:
            result = consent_respond(token, "declined")
            if "error" in result:
                raise HTTPException(status_code=410, detail=result["error"])
            raise HTTPException(status_code=410, detail="locked")
        row.attempts = (row.attempts or 0) + 1
        db.commit()
        return JSONResponse(
            status_code=403,
            content={"detail": "not_enough_correct", "correct": correct, "required": QUIZ_PASS_THRESHOLD},
        )
    finally:
        db.close()


@app.post("/api/respond/{token}/verify-answer")
def verify_challenge(token: str, body: VerifyAnswer):
    row = get_token(token)
    if row is not None and getattr(row, "group_request_id", None):
        return _verify_group_quiz(token, body.answers)
    result = consent_verify_answer(token, body.answer or "")
    if result.get("verified"):
        return result
    err = result.get("error")
    if err == "not_found":
        raise HTTPException(status_code=404, detail="not found")
    if err == "incorrect":
        raise HTTPException(status_code=403, detail="incorrect")
    if err == "locked":
        raise HTTPException(status_code=410, detail="locked")
    raise HTTPException(status_code=410, detail=err)


def _require_verified(token: str):
    row = get_token(token)
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    if not row.verified:
        raise HTTPException(status_code=403, detail="verification_required")


@app.post("/api/respond/{token}/accept")
def accept(token: str):
    _require_verified(token)
    result = consent_respond(token, "accepted")
    if "error" in result:
        raise HTTPException(status_code=410, detail=result["error"])
    return result


@app.post("/api/respond/{token}/decline")
def decline(token: str):
    _require_verified(token)
    result = consent_respond(token, "declined")
    if "error" in result:
        raise HTTPException(status_code=410, detail=result["error"])
    return result



@app.post("/api/respond/{token}/verify")
async def verify(token: str, file: UploadFile = File(...)):
    row = get_token(token)
    if not row:
        raise HTTPException(status_code=404, detail="not found")
    if row.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="expired")
    image_bytes = await file.read()
    result = redact_image(image_bytes, prompt="face")
    return {
        "redacted_url": f"/api/redacted/{os.path.basename(result['redacted_path'])}",
        "boxes": result["boxes"],
    }


@app.get("/api/redacted/{filename}")
def serve_redacted(filename: str):
    path = os.path.join(UPLOAD_REDACTED, filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(path)


def _group_face_boxes(image_bytes: bytes) -> list:
    """Face boxes for the stored group photo. Mock stays deterministic; live uses sam-3.1."""
    if MUSE_MODE == "mock":
        from backend.sam import _mock_boxes
        return _mock_boxes()
    from backend.sam import _live_sam_boxes
    return _live_sam_boxes(image_bytes, "face")


def _group_name_slot_mapping(image_bytes: bytes, names: list, context: str, slot_count: int) -> dict:
    """Map each name to a face-slot index (or None). Mock is deterministic; live uses muse-spark-1.3."""
    if MUSE_MODE != "mock":
        try:
            return _live_name_slot_mapping(image_bytes, names, context, slot_count)
        except Exception:
            pass
    return {name: (i if i < slot_count else None) for i, name in enumerate(names)}


def _live_name_slot_mapping(image_bytes: bytes, names: list, context: str, slot_count: int) -> dict:
    import base64
    from openai import OpenAI
    client = OpenAI(
        base_url="https://api.meta.ai/v1",
        api_key=os.environ["MODEL_API_KEY"],
    )
    b64 = base64.b64encode(image_bytes).decode()
    prompt = (
        "Match each name to a face slot in this group photo. "
        f"Names: {names}. Context: {context}. There are {slot_count} slots (0-based). "
        'Return STRICT JSON only: a list like [{"name": "...", "slot": 0}]. '
        "Use slot null when a name matches no face."
    )
    resp = client.responses.create(
        model="muse-spark-1.3",
        input=[{
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
            ],
        }],
        reasoning={"effort": "medium"},
        max_output_tokens=8192,
    )
    text = resp.output_text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)
    mapping = {name: None for name in names}
    if isinstance(data, dict):
        items = data.items()
    else:
        items = ((e.get("name"), e.get("slot")) for e in data)
    for name, slot in items:
        if name in mapping and isinstance(slot, int) and 0 <= slot < slot_count:
            mapping[name] = slot
    return mapping


def _hometown_from_context(context: str) -> str | None:
    for known in ("Mosul", "Baghdad"):
        lowered = (context or "").lower()
        if known.lower() in lowered:
            return known
    return None


@app.post("/api/submit-group")
async def submit_group(
    raw_text: str = Form(...),
    context: str = Form(...),
    names: str = Form(...),
    quiz: str = Form(...),
    photo: UploadFile | None = None,
    phone_suffix: str | None = Form(None),
    birth_year: int | None = Form(None),
    contact: str | None = Form(None),
):
    try:
        name_list = json.loads(names)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="names must be a JSON list")
    if not isinstance(name_list, list):
        raise HTTPException(status_code=400, detail="names must be a JSON list")
    try:
        quiz_list = json.loads(quiz)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="quiz must be a JSON list of 5 {q, a} objects")
    if (
        not isinstance(quiz_list, list) or len(quiz_list) != 5
        or any(not isinstance(item, dict) or "q" not in item or "a" not in item for item in quiz_list)
    ):
        raise HTTPException(status_code=400, detail="quiz must be a JSON list of 5 {q, a} objects")
    group_id = str(uuid.uuid4())
    photo_path = None
    if photo is not None:
        os.makedirs(UPLOAD_ORIG, exist_ok=True)
        photo_path = os.path.join(UPLOAD_ORIG, f"group_{group_id}.jpg")
        image_bytes = await photo.read()
        with open(photo_path, "wb") as f:
            f.write(image_bytes)
    db = SessionLocal()
    try:
        row = GroupRequest(
            id=group_id,
            raw_text_enc=fernet.encrypt(raw_text.encode()).decode(),
            context_enc=fernet.encrypt(context.encode()).decode(),
            photo_path=photo_path,
            names_json_enc=fernet.encrypt(json.dumps(name_list).encode()).decode(),
            quiz_json_enc=fernet.encrypt(json.dumps(quiz_list).encode()).decode(),
            phone_suffix_enc=fernet.encrypt(phone_suffix.encode()).decode() if phone_suffix else None,
            birth_year=birth_year,
            contact_enc=fernet.encrypt(contact.encode()).decode() if contact else None,
            status="filed",
        )
        db.add(row)
        db.commit()
    finally:
        db.close()
    return {"group_request_id": group_id, "status": "filed"}


@app.post("/api/match-group/{group_request_id}")
def match_group(group_request_id: str):
    db = SessionLocal()
    try:
        group = db.query(GroupRequest).filter(GroupRequest.id == group_request_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="not found")
        names = json.loads(fernet.decrypt(group.names_json_enc.encode()).decode())
        context = fernet.decrypt(group.context_enc.encode()).decode()
        phone_suffix = fernet.decrypt(group.phone_suffix_enc.encode()).decode() if group.phone_suffix_enc else None
        with open("backend/seed_graph.json") as f:
            candidates = json.load(f)
        hometown = _hometown_from_context(context)
        if group.photo_path is not None:
            mode = "photo"
            with open(group.photo_path, "rb") as f:
                image_bytes = f.read()
            boxes = _group_face_boxes(image_bytes)
            slots = [{"slot": i, "box": box} for i, box in enumerate(boxes)]
            mapping = _group_name_slot_mapping(image_bytes, names, context, len(slots))
            slot_to_name = {}
            for name, slot in mapping.items():
                if slot is not None and slot not in slot_to_name:
                    slot_to_name[slot] = name
            slot_names = [(entry["slot"], slot_to_name.get(entry["slot"])) for entry in slots]
        else:
            mode = "names_only"
            slot_names = [(i, name) for i, name in enumerate(names)]
        out_slots = []
        issued = 0
        for slot, name in slot_names:
            if name is None:
                out_slots.append({
                    "slot": slot, "name": None, "candidate_id": None,
                    "score": 0.0, "threshold_met": False, "token_issued": False,
                })
                continue
            seeker = {
                "name": name, "hometown": hometown, "phone_suffix": phone_suffix,
                "birth_year": group.birth_year, "contacts": [],
            }
            ranked = rank_candidates(seeker, candidates)
            top = ranked[0]
            met = threshold_met(top["score"])
            token_issued = False
            if met:
                token = secrets.token_urlsafe(32)
                db.add(ConsentToken(
                    id=str(uuid.uuid4()),
                    match_id="pending",
                    token=token,
                    request_id=None,
                    candidate_id=top["candidate_id"],
                    expires_at=datetime.utcnow() + timedelta(hours=24),
                    used="false",
                    response="pending",
                    challenge_answer_enc=None,
                    verified=False,
                    attempts=0,
                    group_request_id=group_request_id,
                    slot_index=slot,
                ))
                token_issued = True
                issued += 1
            out_slots.append({
                "slot": slot, "name": name, "candidate_id": top["candidate_id"],
                "score": top["score"], "threshold_met": met, "token_issued": token_issued,
            })
        group.status = "matched" if issued else "filed"
        db.commit()
        status = group.status
    finally:
        db.close()
    return {"group_request_id": group_request_id, "status": status, "mode": mode, "slots": out_slots}


@app.get("/api/group-status/{group_request_id}")
def group_status(group_request_id: str):
    db = SessionLocal()
    try:
        group = db.query(GroupRequest).filter(GroupRequest.id == group_request_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="not found")
        tokens = db.query(ConsentToken).filter(ConsentToken.group_request_id == group_request_id).all()
        confirmed = sum(1 for t in tokens if t.response == "accepted")
        pending = sum(1 for t in tokens if t.response == "pending" and t.used == "false")
        declined = sum(1 for t in tokens if t.response == "declined")
    finally:
        db.close()
    return {"confirmed": confirmed, "pending": pending, "declined": declined}


@app.get("/api/group-confirmed/{group_request_id}")
def group_confirmed(group_request_id: str):
    db = SessionLocal()
    try:
        group = db.query(GroupRequest).filter(GroupRequest.id == group_request_id).first()
        if not group:
            raise HTTPException(status_code=404, detail="not found")
        names = json.loads(fernet.decrypt(group.names_json_enc.encode()).decode())
        tokens = db.query(ConsentToken).filter(
            ConsentToken.group_request_id == group_request_id,
            ConsentToken.response == "accepted",
        ).all()
        slots = []
        for t in tokens:
            name = names[t.slot_index] if t.slot_index is not None and 0 <= t.slot_index < len(names) else None
            recent_url = (
                f"/api/redacted/{os.path.basename(t.recent_photo_path)}"
                if t.recent_photo_path else None
            )
            slots.append({
                "slot_index": t.slot_index,
                "name": name,
                "recent_photo_url": recent_url,
                # channel_id is reserved for a future channel-opening flow.
                "channel_id": None,
            })
    finally:
        db.close()
    return {"group_request_id": group_request_id, "slots": slots}


@app.post("/api/respond/{token}/recent-photo")
async def recent_photo(token: str, file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        row = db.query(ConsentToken).filter(ConsentToken.token == token).first()
        if not row:
            raise HTTPException(status_code=404, detail="not found")
        if row.expires_at < datetime.utcnow():
            raise HTTPException(status_code=410, detail="expired")
        if row.used == "true":
            raise HTTPException(status_code=410, detail="already used")
        if not row.verified:
            raise HTTPException(status_code=403, detail="verification_required")
        image_bytes = await file.read()
        result = redact_image(image_bytes, prompt="face")
        row.recent_photo_path = result["redacted_path"]
        db.commit()
        filename = os.path.basename(result["redacted_path"])
    finally:
        db.close()
    return {"redacted_url": f"/api/redacted/{filename}"}