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

Task 7 — Add ground-truth verification line to Admin.jsx

Add a verification line to `frontend/src/screens/Admin.jsx` that compares the
match result against the seed graph's expected outcome.

Requirements:

- Compute a `verificationStatus` with three states:
  - `verified`: `match.threshold_met === true` AND `match.winner_id === 'c1'`
  - `unexpected`: `match.threshold_met === true` AND `match.winner_id !== 'c1'`
  - `no_match`: `match.threshold_met === false`
- Render the verification line **between the ranked table and the JSON block**:
  - `verified` → green background `#e8f5e9`, green left border `#0a7a2f`,
    green text `#0a7a2f`, text: "✅ VERIFIED against ground truth: winner is c1,
    threshold met, traps correctly below 0.72."
  - `unexpected` → red background `#fdecec`, red left border `#b00020`,
    red text `#b00020`, text: "⚠️ UNEXPECTED: winner is {winner_id}.
    Seed graph expects c1."
  - `no_match` → gray background `#f5f5f5`, gray left border `#666`,
    dark text `#333`, text: "ℹ️ No match above threshold. This is the
    correct behavior for unrelated input."
- Font size 15px, padding `10px 14px`, border radius 4px.
- Add `setToken(null)` inside `runMatch` so a new match clears the old token.
- Do not change the ranked table, the JSON block, the issue-token button, or
  the recipient link.
- Do not touch the backend.

Validation:

- `npm run lint` passes in `frontend/`.
- Live check with matching input ("my sister Layla, Mosul, phone 4471, born 1988")
  shows the green VERIFIED line.
- Live check with unrelated input ("uncle Bob from Lagos, phone 1234, born 1960")
  shows the gray "No match" line.
- Readback confirms all three states render with distinct colors.

Task 7 — Ground-truth verification line in Admin.jsx

Add a verification line to frontend/src/screens/Admin.jsx between the ranked
table and the JSON block.

    Compute verificationStatus with three states:

        verified: match.threshold_met === true AND match.winner_id === 'c1'

        unexpected: match.threshold_met === true AND match.winner_id !== 'c1'

        no_match: match.threshold_met === false

    Render:

        verified → background #e8f5e9, border-left 4px solid #0a7a2f,
        color #0a7a2f, text: "✅ VERIFIED against ground truth: winner is c1,
        threshold met, traps correctly below 0.72."

        unexpected → background #fdecec, border-left 4px solid #b00020,
        color #b00020, text: "⚠️ UNEXPECTED: winner is {winner_id}. Seed graph
        expects c1."

        no_match → background #f5f5f5, border-left 4px solid #666,
        color #333, text: "ℹ️ No match above threshold. This is the correct
        behavior for unrelated input."

    Font size 15px, padding 10px 14px, border-radius 4px.

    Add setToken(null) inside runMatch so a new match clears the old token.

    Do not change the ranked table, JSON block, issue-token button, or recipient link.

Validation: npm run lint passes; both green and gray states render in the
browser with matching input and unrelated input.

Scope restriction: FRONTEND ONLY. Do not open or modify any file in backend/.
Task 8a — Challenge question clarity (frontend)

Replace the existing challenge question block in
frontend/src/screens/Respond.jsx with a version that:

    Shows the hint (71) in the question — the recipient confirms
    recognition, they do not recall from memory.

    Explicitly offers declining as safe — no guilt, no pressure.

    Is honest about what happens either way.

Replace the current challenge question paragraph with this block:
jsx

<div style={{
  marginTop: 20,
  padding: 16,
  background: '#fff8e1',
  borderLeft: '4px solid #f9a825',
  borderRadius: 4,
}}>
  <p style={{ margin: 0, fontWeight: 700, fontSize: 15 }}>
    One verification step
  </p>
  <p style={{ margin: '8px 0', fontSize: 15 }}>
    The seeker remembers a phone number ending in{' '}
    <strong style={{ fontSize: 18, letterSpacing: 2 }}>71</strong>.
    If you have ever used a phone number with those last two digits,
    enter them below.
  </p>
  <p style={{ margin: '4px 0 12px', fontSize: 13, color: '#666' }}>
    If you don't remember, you can decline. The seeker will not be
    notified either way.
  </p>
</div>

Do not change the input, the Verify button, the error messaging, or the
Accept/Decline gating logic.

Validation: npm run lint passes; the question shows the hint; declining
is visible as a safe option.

Scope restriction: FRONTEND ONLY. Change Respond.jsx only.
Task 8b — Individual visual verification (frontend)

Add an optional "Upload a photo that connects you to this request" step in
frontend/src/screens/Respond.jsx, placed between the challenge question
and the Accept/Decline buttons.

    Accepted formats: image/*

    On upload, call the existing POST /api/respond/{token}/verify route
    (already implemented; runs SAM 3.1 with prompt "face").

    The recipient sees the redacted preview only (existing behavior).

    Uploading a photo is optional — the challenge question alone unlocks
    Accept/Decline.

    The seeker NEVER sees the original photo.

Validation: npm run lint passes; upload shows redacted preview; accept/decline
still work without upload.

Scope restriction: FRONTEND ONLY. Change Respond.jsx only. Do not modify
backend/sam.py, backend/main.py, or the existing /api/respond/{token}/verify
route — they already work.

Task 9 — Group request scaffolding (backend only)

Add the group flow alongside the individual one. Shares `ConsentToken` and
the existing `/api/respond/{token}` route.

#### Models

New `GroupRequest` in `backend/models.py`:

- `id` (String, PK, UUID)
- `created_at` (DateTime)
- `raw_text_enc` (String, Fernet ciphertext)
- `context_enc` (String, Fernet ciphertext — e.g. "2005 Methodist High School, Lagos")
- `photo_path` (String, **nullable** — path in `uploads/original/`, never served;
  NULL when the seeker did not upload a photo)
- `names_json_enc` (String, Fernet ciphertext — JSON array of names the seeker typed)
- `quiz_json_enc` (String, Fernet ciphertext — JSON array of exactly 5 objects,
  each `{"q": "<question>", "a": "<answer>"}`)
- `phone_suffix_enc` (String, nullable — Fernet ciphertext, seeker's remembered phone tail)
- `birth_year` (Integer, nullable — approximate class year, not PII)
- `contact_enc` (String, nullable — Fernet ciphertext)
- `status` (String, default `"filed"` — `filed | matched | partial | complete | expired`)

Extend `ConsentToken` in `backend/models.py` with three nullable columns:

- `group_request_id` (String, nullable)
- `slot_index` (Integer, nullable)
- `recent_photo_path` (String, nullable — path to the SAM-redacted recent photo,
  in `uploads/redacted/`. Never the original.)

Relax `ConsentToken.request_id` and `ConsentToken.candidate_id` to nullable
so group tokens can leave `request_id` empty while storing the matched
`candidate_id`. A token with `request_id` set = individual. A token with
`group_request_id` set = group.

#### Routes in `backend/main.py`

**`POST /api/submit-group`** — multipart form with fields:

- `raw_text` (str)
- `context` (str)
- `names` (JSON string of list of names)
- `quiz` (JSON string of exactly 5 `{q, a}` objects)
- `photo` (UploadFile, **optional**)
- `phone_suffix` (str, optional)
- `birth_year` (int, optional)
- `contact` (str, optional)

Behavior:
- If photo is provided: store at `uploads/original/group_{id}.jpg` (never served),
  set `photo_path`
- If photo is omitted: `photo_path = None`, skip file write
- Encrypt all PII with Fernet (`raw_text_enc`, `context_enc`,
  `names_json_enc`, `quiz_json_enc`, `phone_suffix_enc`, `contact_enc`)
- `birth_year` stays plaintext integer (not PII)
- Insert `GroupRequest` with status `"filed"`
- Return `{"group_request_id": id, "status": "filed"}`

**`POST /api/match-group/{group_request_id}`** — runs the group pipeline:

1. Load the group request; decrypt `names`, `context`, and optional
   `phone_suffix`, `birth_year`, `contact`
2. **If `photo_path` is not None (photo mode):**
   a. Call `sam-3.1` with prompt `"face"` on the stored photo → get face boxes.
      Store as anonymous slots `[{"slot": 0, "box": {...}}, ...]`
   b. Call `muse-spark-1.3` with the image + names + context, asking for a
      JSON mapping `{"name": "...", "slot": N}` for each name. Unmapped names
      get `slot: null`. **Mock branch must be deterministic**: name[i] → slot i
   c. For each name with a non-null slot, build seeker dict and rank
3. **If `photo_path` is None (names_only mode):**
   a. Skip SAM and Muse Spark image calls entirely
   b. Each name in `names` becomes a slot at its index: `slot = i`, `name = names[i]`
   c. For each name, build seeker dict and rank
4. In both modes, for each slot whose top score ≥ 0.72, create a ConsentToken
   with:
   - `group_request_id` set
   - `slot_index` set
   - `request_id` = NULL
   - `candidate_id` set to the matched candidate
   - `verified` = false
   - `attempts` = 0
   - `expires_at` = now + 24h
   - `challenge_answer_enc` = NULL (the quiz lives on GroupRequest)
5. Update `GroupRequest.status` to `"matched"` if at least one token was issued,
   `"filed"` if none
6. Return:
```json
{
  "group_request_id": "...",
  "status": "matched",
  "mode": "photo" | "names_only",
  "slots": [
    {"slot": 0, "name": "Chidi", "candidate_id": "c1",
     "score": 0.85, "threshold_met": true, "token_issued": true},
    {"slot": 1, "name": "Ngozi", "candidate_id": null,
     "score": 0.0, "threshold_met": false, "token_issued": false}
  ]
}

GET /api/group-status/{group_request_id} — returns counts only:
json

{"confirmed": 2, "pending": 3, "declined": 1}

    confirmed = tokens with response = "accepted"

    pending = tokens with response = "pending" and used = false

    declined = tokens with response = "declined"

    Never return names.

GET /api/group-confirmed/{group_request_id} — returns confirmed slots only,
each with:

    slot_index

    name (from the seeker's own names list at that index — never the recipient's name)

    recent_photo_url (the redacted recent photo, or null if not uploaded)

    channel_id (or null if no channel opened yet)

The seeker uses this to compare the redacted recent photo against their own
group photo. The seeker makes the final judgment. The recipient is never told
the outcome unless a channel is opened.
Extend GET /api/respond/{token} for group tokens

If the token has group_request_id set, the response must include:

    redacted_summary: "A former classmate is looking for people from
    [decrypted context]. You appear to be [name] in a group photo they filed."
    where [name] comes from the group request's names_json_enc at
    slot_index

    quiz: JSON array of the 5 questions (decrypted from quiz_json_enc),
    with answers stripped out — answers never leave the server

    pass_threshold: 4

    expires_at: same as before

Individual tokens return the existing shape unchanged (no quiz key).
Extend POST /api/respond/{token}/verify-answer for group tokens

For group tokens:

    Load the token's group_request_id → load the group → decrypt quiz_json_enc

    Accept a JSON body: {"answers": ["answer1", "answer2", "answer3", "answer4", "answer5"]}

    Compare each answer to the stored answer (case-insensitive, trimmed)

    Count matches

    If correct >= 4:

        Set token.verified = true

        Return {"verified": true, "correct": N, "required": 4}

    If correct < 4 and this is the first failure for this token:

        Increment attempts

        Return 403 {"detail": "not_enough_correct", "correct": N, "required": 4}

        Do NOT reveal which answers were wrong — only the total count

    If correct < 4 and attempts >= 1 (second failure):

        Call consent_respond(token, "declined") to close the token silently

        Return 410 {"detail": "locked"}

For individual tokens:

    Keep the existing single-answer behavior unchanged

New route — POST /api/respond/{token}/recent-photo

After the recipient has passed the quiz (token.verified = true) but before
accept/decline:

    Accept a photo UploadFile

    Run SAM 3.1 with prompt "face" on the uploaded image

    Store the original in uploads/original/ (never served)

    Store the SAM-redacted version in uploads/redacted/

    Set token.recent_photo_path to the redacted path

    Return {"redacted_url": "/api/redacted/{filename}"} so the recipient can
    see their own preview

The recipient's recent photo is optional — they can accept or decline
without uploading one.

Important design note: SAM 3.1 redacts faces but does not perform
face recognition. The system does not automatically compare the recipient's
recent photo to the group photo. The seeker makes that comparison by eye,
using /api/group-confirmed/{id}. This is the correct design for a
high-stakes family reconnection case — the human is the judge, not the model.
Shared rules

    The /api/respond/{token}/verify-answer route dispatches on
    token.group_request_id: if set, use the 4-of-5 quiz path; if not, use
    the existing single-answer path

    Accept/decline reject unverified tokens with 403 (existing behavior,
    unchanged for both individual and group)

    Three wrong attempts still applies to individual tokens; group tokens
    use the two-attempt lockout above

    Decline remains silent for both flows: seeker status stays filed,
    group counts decrement but never name who declined

    There is no route that serves uploads/original/ files —
    the recent photo original is never reachable by any client

Validation

    POST /api/submit-group returns a valid group_request_id

    POST /api/submit-group without a photo returns a valid id and
    photo_path is NULL

    - `POST /api/match-group/{id}` returns the slot array with
  `token_issued: true` for at least one above-threshold slot when the
  submit includes clues that align with a seed candidate. For the
  demo, use `phone_suffix="4471"` and `birth_year=1988` with a name
  that matches a seed candidate (e.g. "Layla") and context that
  includes "Mosul". A 2005 class year (1988 birth year) aligns with
  candidate `c1`; using birth_year=2005 (22 years later) correctly
  fails to match, which is the intended threshold behavior — it proves
  the year weight is doing real work.

    POST /api/match-group/{id} in names_only mode issues tokens without
    calling SAM or Muse Spark, and returns "mode": "names_only"

    POST /api/match-group/{id} in photo mode returns "mode": "photo"

    A group token, opened at GET /api/respond/{token}, returns
    redacted_summary, quiz (questions only, no answers), and
    pass_threshold: 4

    Submitting 4 correct + 1 wrong answer → {"verified": true, "correct": 4}

    Submitting 3 correct + 2 wrong answers twice → first attempt 403 with
    correct count only, second attempt 410 locked

    POST /api/respond/{token}/recent-photo after verify returns a redacted
    URL; before verify returns 403

    GET /api/group-status/{id} returns counts only, never names

    GET /api/group-confirmed/{id} returns confirmed slots with
    recent_photo_url when uploaded, null otherwise

    The individual consent flow still works end-to-end: submit → match →
    single-answer challenge → accept/decline

    uploads/original/group_*.jpg is never served by any route

    uploads/original/ recent photos are never served by any route

    Mock name-to-slot mapping is deterministic (name[i] → slot i)

Scope restriction: BACKEND ONLY. Do not modify frontend in this task.
Do not modify the individual consent flow in Respond.jsx or Seeker.jsx.
Do not add a group UI — that is a future task.


Task 10 — Group request frontend (frontend only)

Build the frontend for the group flow. Backend routes exist from Task 9.

#### New screen: GroupSeeker.jsx

Create `frontend/src/screens/GroupSeeker.jsx`:

- Photo upload input (`accept="image/*"`)
- Context text input (placeholder: "2005 Methodist High School, Lagos")
- Names textarea (placeholder: "Chidi, Ngozi, Emeka (one per line)")
- Unifier question input (placeholder: "What was our form teacher's name?")
- Unifier answer input
- Submit button

On submit:
- Build `FormData` with fields: `raw_text`, `context`, `names` (JSON string of the split list), `unifier_question`, `unifier_answer`, `photo` (the file)
- `axios.post(`${API}/api/submit-group`, formData)`
- **Do NOT** set `Content-Type` manually — let the browser set the boundary
- Show the returned `group_request_id` and a link to `/admin` with the ID pre-filled

#### Extend Admin.jsx

Add a second section (or a toggle) for group requests:

- Input for `group_request_id`
- Button "Run group match" → calls `POST /api/match-group/{id}`
- Display the `slots` array as a table: slot, name, candidate_id, score, threshold_met, token_issued
- Button "Check status" → calls `GET /api/group-status/{id}` → shows confirmed/pending/declined counts

#### Add route in App.jsx

Add `<Route path="/group" element={<GroupSeeker />} />` and a nav link "Group".

#### File upload rule

When sending `FormData` with axios to FastAPI:
- **Do NOT** set `Content-Type` manually to `"multipart/form-data"` — let the browser set it with the boundary
- **Do** append the file with the field name matching the FastAPI parameter name (`photo` → `photo: UploadFile = File(...)`)

Validation:
- `npm run lint` passes
- Uploading a photo + names + context returns a `group_request_id`
- Running group match on that ID returns slot results
- The existing individual flow is unchanged

**Scope restriction: FRONTEND ONLY. Do not modify any backend file.*

One-Line Pitch

    Reunite uses Muse Spark to parse fragmented memories and map faces, Muse
    Wonder to reason through ambiguous candidates, and SAM 3.1 to redact
    verification documents and detect faces in group photos — so privacy is
    provable, not promised — all built with Muse Code on the Standard tier,
    because vulnerable people's data should never train a model.
