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

---

## Commands

```bash
# Backend (from repo root)
uvicorn backend.main:app --reload --port 8000

# Frontend (from frontend/)
cd frontend && npm run dev

# Health check
curl http://localhost:8000/api/health

# Test runbook
# See docs/TESTING.md

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

Critical: reasoning.effort: "none" is REJECTED by Meta. Valid values:
minimal | low | medium | high | xhigh. Use medium for parsing.
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

Critical: Muse Wonder Full is NOT available on the API — only inside Muse
Code subscription plans. Setting reasoning.effort: "max" on muse-wonder-1.0
does NOT give you Full. Do not attempt it.
3. SAM 3.1 — Image Redaction

    Model ID: sam-3.1

    Endpoint: POST /v1/responses

    Job: Detect faces/IDs in verification images, return boxes for black-box redaction

python

client.responses.create(
    model="sam-3.1",
    input=[{
        "type": "message",
        "role": "user",
        "content": [
            {"type": "input_text", "text": "face"},   # ONE short noun phrase
            {"type": "input_image", "image_url": f"data:image/jpeg;base64,{b64}"},
        ],
    }],
)

Critical:

    Prompt must be a single short noun phrase: "face", "ID number",
    "document text". Never "face, ID number" in one call.

    To mask both face and ID, send two separate requests.

    Empty output_text means no match — handle gracefully (do not crash).

Mock / Live Switch

MUSE_MODE in .env controls which path runs:

    mock: _mock_parse / _mock_boxes / mock resolve_ambiguity — no API calls, no cost

    live: calls the real models above

Both paths must remain functional. Never delete the mock branches.
The live branch is the product; the mock branch is for offline development,
unit tests, and demo fallback.
Privacy Rules (Non-Negotiable)

    The seeker never receives the candidate's name, photo, profile link, or
    any direct identifier at any stage — unless the candidate accepts.

    Decline is silent. The seeker's status stays filed. No "declined"
    message, no "seen" status, no indicator that a match was ever found.

    PII encrypted at rest with Fernet. raw_text_enc, contact_enc,
    parsed_json_enc are ciphertext in the DB. Keys live in .env only.

    Verification images stored twice: uploads/original/ (never served) and
    uploads/redacted/ (SAM 3.1 output — the only one served). There is no
    route that serves uploads/original/.

    Consent tokens are signed, single-use, expire in 24h. Reuse returns 410.

    There is no public search endpoint. Matching is server-side only.

    Standard tier only. No -contributor model IDs.

    Logs never contain PII. Log request IDs, scores, status transitions only.

If a task would violate any of the above, stop and ask rather than implementing.
Matching Weights (Do Not Change Without Instruction)
Feature	Weight
Phone suffix (last 4)	0.30
Hometown (Jaro-Winkler)	0.20
Alias / maiden name (Double Metaphone)	0.20
Birth year proximity (±2 full, ±8 zero)	0.15
Shared contact overlap (Jaccard)	0.10

Threshold: 0.72. Ambiguity gap: 0.05.
Current Task List

Complete these in order. Use /plan before each and wait for approval.
Task 1 — Verify live branches use correct model IDs

Confirm and fix if needed:

    _live_parse in backend/muse.py calls muse-spark-1.3

    _live_resolve in backend/muse.py calls muse-wonder-1.0

    _live_sam_boxes in backend/sam.py calls sam-3.1 with a single-noun-phrase prompt

Task 2 — Fix _mock_parse to respect input

Extract keywords from raw_text (name, hometown, phone suffix, birth year)
instead of returning fixed values. This makes the UI show correct non-matches
for inputs that don't fit the seed graph.
Task 3 — Add ranked array to /api/match response

In backend/main.py, return the full ranked list (candidate_id, score,
breakdown) so the admin panel can show every candidate, not just the winner.
Task 4 — Add ranked candidates table to Admin.jsx

Show each candidate's score and whether it is above or below the 0.72 threshold.
This is the "engine is real" proof for judges.
Task 5 — Add privacy message to Seeker.jsx

After submission, show: "Your request is encrypted. The person being sought
will receive a private notification. If they decline, you will not be told —
that is how we protect them."
Task 6 — Add challenge question to Respond.jsx + backend route

Add POST /api/respond/{token}/verify-answer in backend/main.py. Wrong answer
triggers silent decline (call consent_respond(token, "declined")) and returns

    Frontend shows the question between the redacted summary and Accept/Decline.

When Working on This Project

Always do this sequence:

    Read this AGENTS.md and the relevant files before changing anything.

    Use /plan — propose the change as a plan before editing any file.

    Preserve mock branches — never remove the MUSE_MODE == "mock" path.

    Never add a -contributor model ID.

    Never add a route that serves uploads/original/.

    Never make decline visible to the seeker in any response or status field.

    Commit small — one feature, one commit message that names the feature.

Do Not Do

    Do not invent new routes without being asked.

    Do not change scoring weights or the 0.72 threshold.

    Do not add image-analysis features to SAM (redaction is the only use).

    Do not use Muse Wonder for anything except the ambiguity tie-break.

    Do not build photo perceptual-hash matching (explicitly cut from scope).

    Do not integrate Twilio, Messenger Platform API, or any external notification
    service — the entire consent loop is in-app.

One-Line Pitch

    Reunite uses Muse Spark to parse fragmented memories into matching clues,
    Muse Wonder to reason through ambiguous candidates, and SAM 3.1 to redact
    verification documents so privacy is provable — not promised — all built
    with Muse Code on the Standard tier, because vulnerable people's data should
    never train a model.

If Something Is Missing

If a task requires a detail not covered here:

    Search backend/, frontend/src/, and docs/ first.

    If still unclear, stop and ask — do not invent behavior that could
    violate the privacy rules above.
Muse Code reads this file as project rules when it runs in this directory.

## Project

- Name: Reunite
- Generated by `muse init`.

## Common Commands

- No standard build or test commands detected yet.

## Project Layout

- `docs/`: Project docs.
