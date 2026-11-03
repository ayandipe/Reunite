# AGENTS.md — Reunite

## Project Overview

**Reunite** is a privacy-first family reconnection bridge for families or friends separated by war and displacement. Supports two entry paths — individual (find one person) and group (reassemble a cohort) — sharing the same engine.

A displaced person files a confidential request. Meta's AI parses memories, matches blind against profiles, and notifies the person being sought. The seeker NEVER sees who was found unless consent is given. Decline is silent.

- Track: Indie Developer
- Theme: Build for Your World
- Stack: FastAPI + SQLite (backend) · React + Vite (frontend)

## Commands

Backend: `uvicorn backend.main:app --reload --port 8000` (from repo root)
Frontend: `cd frontend && npm run dev`
Health: `curl http://localhost:8000/api/health`

## The Three Meta Models

Base URL: https://api.meta.ai/v1
Auth: Bearer $MODEL_API_KEY
Tier: Standard only. Never use -contributor.

### Muse Spark 1.3 — Parsing
- Model ID: muse-spark-1.3
- Endpoint: POST /v1/responses
- Job: Parse free-text memory into structured JSON
- Call: reasoning={"effort": "medium"}, max_output_tokens=8192
- reasoning.effort "none" is REJECTED

### Muse Wonder 1.0 — Ambiguity Resolution
- Model ID: muse-wonder-1.0
- Endpoint: POST /v1/responses
- Job: Choose between candidates within 0.05
- Call: reasoning={"effort": "high"}, max_output_tokens=64
- Muse Wonder Full is NOT available on API

### SAM 3.1 — Image Redaction
- Model ID: sam-3.1
- Endpoint: POST /v1/responses
- Job: Detect faces/IDs in verification images
- Prompt must be ONE short noun phrase ("face")
- Empty output_text means no match

## Mock / Live Switch

MUSE_MODE in .env: mock (no API calls) or live (real models). Both paths functional. Never delete mock branches.

## Privacy Rules (Non-Negotiable)

1. Seeker never receives candidate name, photo, profile link, or direct identifier unless candidate accepts.
2. Decline is silent. Seeker status stays filed.
3. PII encrypted at rest with Fernet. Keys in .env only.
4. Verification images stored twice: uploads/original/ (never served) and uploads/redacted/ (SAM output — only one served).
5. Consent tokens: signed, single-use, 24h expiry.
6. No public search endpoint. Matching server-side only.
7. Standard tier only.
8. Logs never contain PII.

## Matching Weights (Do Not Change)

| Feature | Weight |
|---------|--------|
| Phone suffix (last 4) | 0.30 |
| Hometown (Jaro-Winkler) | 0.20 |
| Alias/maiden (Double Metaphone) | 0.20 |
| Birth year proximity | 0.15 |
| Shared contact overlap | 0.10 |

Threshold: 0.72. Ambiguity gap: 0.05.

## Completed Tasks

All tasks 1-11 are complete. Current state:

### Backend (backend/)
- models.py: SeekerRequest, ConsentToken (with verified, attempts, group_request_id, slot_index, recent_photo_path, challenge_answer_enc), GroupRequest (with quiz_json_enc, photo_path nullable, phone_suffix_enc, birth_year, contact_enc), Channel (with recipient_contact_enc, seeker_confirmed, contact_revealed), ChannelMessage
- main.py: All routes — /api/submit, /api/match, /api/consent, /api/respond/{token}, /api/respond/{token}/verify-answer, /api/respond/{token}/accept, /api/respond/{token}/decline, /api/respond/{token}/verify, /api/respond/{token}/recent-photo, /api/submit-group, /api/match-group, /api/group-status, /api/group-confirmed, /api/channel/{id}, /api/channel/{id}/confirm-seeker, /api/channel/{id}/share-contact, /api/channel/{id}/message, /api/channel/{id}/messages, /api/redacted/{filename}
- matching.py: rank_candidates, is_ambiguous, threshold_met
- muse.py: parse_memory, resolve_ambiguity (mock/live branches)
- sam.py: redact_image, _parse_boxes (regex fixed for |box;...;w=;h=| format)
- consent.py: create_token, verify_answer, respond
- seed_graph.json: 15 candidates including c1, c1_twin, c_trap_a, c_trap_b

### Frontend (frontend/src/screens/)
- Seeker.jsx: Submission form, filed confirmation with Refresh status
- Respond.jsx: Redacted summary, challenge question (hint 71), photo upload, Accept/Decline (no contact toggle — moved to Channel)
- Admin.jsx: Individual match (ranked table + VERIFIED line + JSON), group match (slots table + token_url links + Check status)
- Channel.jsx: Chat with sender distinction (seeker left/blue, recipient right/green), payment gate ($5.99 modal before confirm), share request after payment (recipient), contact reveal, contact scrubbing
- GroupSeeker.jsx: Group form, silent auto-match on submit, minimal confirmation (filed + ID + Refresh status)
- App.jsx: Routes for /, /admin, /respond/:token, /channel/:channelId, /group

## Demo Flow (Current Behavior)

### Individual
1. Seeker submits at / → Muse Spark parses → token issued
2. Admin runs match at /admin → ranked table shows c1/0.85 + traps below 0.72
3. Issue consent token → recipient link
4. Recipient opens /respond/{token} → hint 71 → answer → verify → photo upload optional → Accept
5. Channel opens at /channel/{id}?viewer=recipient
6. Seeker opens /channel/{id}?viewer=seeker → payment gate ($5.99)
7. Recipient sees share request → shares contact → seeker sees contact
8. Both chat; contact scrubbing blocks phone/email/URL in messages

### Group
1. Seeker submits at /group → silent POST /api/match-group
2. Confirmation shows "filed" + group ID + Refresh status button
3. Admin at /admin pastes group ID → Run group match → slots table with token_url links
4. Each issued slot has "Open recipient view →" link
5. Recipient opens /respond/{token} → 5-question quiz → 4/5 pass → Accept
6. Counts update via /api/group-status

## Rules for Future Work

1. Read this AGENTS.md and relevant files before changing anything
2. Use /plan before editing any file
3. Preserve mock branches
4. Never add -contributor model IDs
5. Never serve uploads/original/
6. Never make decline visible to the seeker
7. Commit small

## Do Not

- Change scoring weights or 0.72 threshold
- Add image-analysis to SAM (redaction + face detection only)
- Use Muse Wonder for anything except ambiguity tie-break
- Integrate external notification services (Twilio, Messenger Platform API)
- Touch group quiz flow (working)

## One-Line Pitch

Reunite uses Muse Spark to parse fragmented memories and map faces, Muse Wonder to reason through ambiguous candidates, and SAM 3.1 to redact verification documents and detect faces in group photos — so privacy is provable, not promised — all built with Muse Code on the Standard tier, because vulnerable people's data should never train a model.
