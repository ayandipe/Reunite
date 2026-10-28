# AGENTS.md — Reunite

## Project Overview

**Reunite** is a privacy-first family reconnection bridge for families or friends
separated by war and displacement.

A displaced person files a confidential request with fragmented memories. Meta's
AI parses those memories, matches them blind against candidate profiles, and
notifies the person being sought. The seeker NEVER sees who was found unless the
sought person explicitly consents. **Decline is silent.**

- Track: Indie Developer
- Theme: Build for Your World
- Stack: FastAPI + SQLite (backend) · React + Vite (frontend)

## Commands

```bash
# Backend (from repo root)
uvicorn backend.main:app --reload --port 8000

# Frontend (from frontend/)
cd frontend && npm run dev

# Health check
curl http://localhost:8000/api/health

# Test runbook: see docs/TESTING.md

The Three Meta Models — First Source of Truth

Every live-mode path MUST call these exact model IDs. Mock files are the
fallback; live mode is the product.

Base URL: https://api.meta.ai/v1
Auth: Authorization: Bearer $MODEL_API_KEY
Tier: Standard only. Never use a model ID ending in -contributor.
1. Muse Spark 1.3 — Parsing

    Model ID: muse-spark-1.3

    Endpoint: POST /v1/responses

    Job: Parse free-text memory → structured JSON clues

python

client.responses.create(
    model="muse-spark-1.3",
    input="<prompt asking for strict JSON with name, relationship, hometown, "
          "phone_suffix, birth_year, confidence>",
    reasoning={"effort": "medium"},
    max_output_tokens=8192,
)

reasoning.effort: "none" is REJECTED. Valid: minimal | low | medium | high | xhigh.
2. Muse Wonder 1.0 — Ambiguity Resolution

    Model ID: muse-wonder-1.0

    Endpoint: POST /v1/responses

    Job: Choose between two candidates when scores differ by < 0.05

python

client.responses.create(
    model="muse-wonder-1.0",
    input="<seeker clues + Candidate A + Candidate B, ask for 'A' or 'B' only>",
    reasoning={"effort": "high"},
    max_output_tokens=10,
)

Muse Wonder Full is NOT available on the API. Do not attempt it.
3. SAM 3.1 — Image Redaction

    Model ID: sam-3.1

    Endpoint: POST /v1/responses

    Job: Detect faces/IDs in verification images

python

client.responses.create(
    model="sam-3.1",
    input=[{
        "type": "message",
        "role": "user",
        "content": [
            {"type": "input_text", "text": "face"},
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
        ],
    }],
)

Prompt must be a single short noun phrase. Never "face, ID number" in one call.
Empty output_text means no match — handle gracefully.
Mock / Live Switch

MUSE_MODE in .env controls which path runs:

    mock: _mock_parse / _mock_boxes / mock resolve_ambiguity — no API calls

    live: calls the real models above

Both paths must remain functional. Never delete the mock branches.
Privacy Rules (Non-Negotiable)

    The seeker never receives the candidate's name, photo, profile link, or
    any direct identifier — unless the candidate accepts.

    Decline is silent. The seeker's status stays filed. No "declined"
    message, no "seen" status.

    PII encrypted at rest with Fernet. Keys live in .env only.

    Verification images stored twice: uploads/original/ (never served) and
    uploads/redacted/ (SAM 3.1 output — the only one served).

    Consent tokens are signed, single-use, expire in 24h. Reuse returns 410.

    No public search endpoint. Matching is server-side only.

    Standard tier only. No -contributor model IDs.

    Logs never contain PII.

If a task would violate any of the above, stop and ask.
Matching Weights (Do Not Change)
Feature	Weight
Phone suffix (last 4)	0.30
Hometown (Jaro-Winkler)	0.20
Alias / maiden name (Double Metaphone)	0.20
Birth year proximity (±2 full, ±8 zero)	0.15
Shared contact overlap (Jaccard)	0.10

Threshold: 0.72. Ambiguity gap: 0.05.
Current Task List

Tasks 1–5 are complete. Only Task 6 remains.
Task 6 — Add challenge question to Respond.jsx + backend route

Add POST /api/respond/{token}/verify-answer in backend/main.py.

Requirements:

    The correct answer is derived from the seeker's parsed phone_suffix
    (last two digits), NOT hardcoded. Store it on the ConsentToken row as
    challenge_answer_enc when the token is created.

    Add an attempts column (integer, default 0) to ConsentToken.

    Wrong answer returns 403 with {"detail": "incorrect"}, increments
    attempts, and does NOT consume the token (allow retry).

    After 3 failed attempts, close the token as declined (silent) and return 410.

    Correct answer returns {"verified": true} and unlocks Accept/Decline.

    Frontend shows the question between the redacted summary and Accept/Decline.

    Question text: "To confirm this request is for you, enter the last two
    digits of a phone number you have used."

When Working on This Project

    Read this AGENTS.md and relevant files before changing anything.

    Use /plan — propose the change before editing any file.

    Preserve mock branches.

    Never add a -contributor model ID.

    Never serve uploads/original/.

    Never make decline visible to the seeker.

    Commit small.

Do Not Do

    Do not invent new routes without being asked.

    Do not change scoring weights or the 0.72 threshold.

    Do not add image-analysis features to SAM.

    Do not use Muse Wonder for anything except ambiguity tie-break.

    Do not integrate Twilio, Messenger Platform API, or external notification service.

One-Line Pitch

    Reunite uses Muse Spark to parse fragmented memories into matching clues,
    Muse Wonder to reason through ambiguous candidates, and SAM 3.1 to redact
    verification documents so privacy is provable — not promised — all built
    with Muse Code on the Standard tier, because vulnerable people's data should
    never train a model.