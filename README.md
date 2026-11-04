# Reunite

> **[▶ Watch the 3-minute demo](https://www.youtube.com/watch?v=YK5_PkJwPig)**



**A privacy-first reconnection bridge for families or friends separated by war, migration, or crisis.**

Consent, not search, is the only key that opens the door.





## The Problem

Search for a person on Facebook, Instagram, or WhatsApp today, and you get dozens of closely related results. Same name. Similar profile. Similar face. You cannot tell which one is the person you are looking for. People send friend requests to the wrong profile every day — they land on a clone, a scammer, or someone who simply shares the same name.

Social media was built for meeting new acquaintances. But there is a category of search it was never designed for — the search for someone you lost. A family member. A friend. A classmate. A whole community, scattered by war, migration, or crisis.

There is no secure, consent-first framework to turn a desperate search into a safe connection.

---

## The Solution

Reunite is a privacy-first reconnection bridge built on Meta's AI. It is a **Blind Notification Bridge**, not a search engine.

A displaced person files a confidential request with fragmented memories — a name, a hometown, a phone number tail, a birth year. They never see a list of profiles. The system matches in the background. The person being sought receives a private, redacted notification. They see only what they need to recognize themselves. They choose to accept — or to decline.

"The candidate graph is four mock profiles. Everything downstream — the scoring, the threshold, the Muse Wonder tie-break, the consent gate, the payment flow — is real code doing real work on those four profiles. If Meta plugged in their actual social graph tomorrow, the engine would work identically — it's just four profiles instead of two billion."

**If they decline, the seeker is never told a match was ever found.** That is the privacy guarantee.

---

## How It Works

### Individual Flow — Find One Person

1. **Seeker files** — a woman displaced from Mosul submits: *"My sister Layla, near old market in Mosul, phone ended 4471, born 1988."* Her memory is encrypted with Fernet at rest.
2. **Muse Spark parses** — the free-text memory becomes structured JSON clues: `{name: "Layla", hometown: "Mosul", phone_suffix: "4471", birth_year: 1988}`.
3. **The engine matches** — five weighted features score every candidate. Real match `c1` scores 0.85. Two trap candidates correctly score below the 0.72 threshold (0.65 and 0.575) on different features — proof the weighting is doing real work.
4. **Muse Wonder decides** — when two candidates fall within 0.05 of each other, Muse Wonder reasons through the conflict and picks a winner.
5. **A consent token is issued** — signed, single-use, 24-hour expiry.
6. **Recipient sees only a redacted summary** — *"A seeker is looking for a sibling last seen near Mosul. They remember the last four digits of a phone number ending in 4471."* No seeker name, no photo, no contact.
7. **Challenge question** — the recipient confirms recognition (not recall) by entering the last two digits of a phone number they've used. Wrong answers allow retries; three failures close the token silently.
8. **Optional photo upload** — SAM 3.1 redacts the face before storage. The original never leaves the server. Only the redacted version is ever served.
9. **Accept or Decline** — Accept opens a secure channel. Decline leaves the seeker's status unchanged. **Silence is the privacy guarantee.**

### Group Flow — Reassemble a Cohort

1. **Seeker files a group request** — a survivor of the 2005 Methodist High School class submits a group photo (optional), names, and **five questions only their cohort would know**.
2. **Silent auto-match** — the system runs the match immediately. The user sees only *"Your group request has been filed. You will be notified if any group member accepts."*
3. **SAM 3.1 finds faces** — if a group photo was uploaded, SAM returns anonymous face slots. If not, names become slots directly.
4. **Muse Spark maps names to faces** — probabilistic matching that guides the seeker's own judgment.
5. **The engine scores per person** — each named slot runs through the same `rank_candidates` pipeline.
6. **Tokens issued per matched person** — each gets their own consent token, their own redacted summary, their own 5-question quiz.
7. **4-of-5 pass rule** — the recipient must answer at least four of five cohort questions correctly. Three or fewer closes the token silently. The response never reveals which answers were wrong.
8. **The seeker sees counts only** — "Confirmed: 1 · Pending: 2 · Declined: 0" — never names, never identities, until each person chooses to open a channel.

### Secure Channel — After Consent

Once a recipient accepts:

1. **Chat UI opens** — both parties can message. Seeker messages appear left-aligned with a blue sender label. Recipient messages appear right-aligned with a green sender label. Contact details in messages are blocked by regex — **contact exchange happens only through the payment-gated reveal**.
2. **The seeker confirms identity** — *"I confirm this is the person I was looking for"* opens a **$5.99 connection fee mockup** (Stripe or Meta Pay in production, simulated in the demo).
3. **The recipient approves contact sharing** — only after payment, the recipient sees: *"The seeker has paid the connection fee and confirmed they are looking for you. Share your contact?"* They can share or keep private. **The payment unlocked the request, not the contact.**
4. **Contact reveals** — if shared, the seeker sees the recipient's contact. If not, the seeker sees: *"The recipient has not shared a contact yet. You can still message them here."*

---

## The Three Meta Models

| Model | Role | Key Detail |
|---|---|---|
| **Muse Spark 1.3** | Parses fragmented memories; maps names to faces in group photos | Standard tier only. `reasoning.effort: "medium"`, `max_output_tokens: 8192` |
| **Muse Wonder 1.0** | Resolves ambiguous matches when candidates fall within 0.05 | `reasoning.effort: "high"`, `max_output_tokens: 64`. Muse Wonder Full is not available on API |
| **SAM 3.1** | Detects and redacts faces/IDs in verification images; finds faces in group photos | Prompt must be a single short noun phrase. Standard tier: $2.50 per 1,000 images |

All three models were smoke-tested live against the Meta Model API Standard tier. See [`docs/TESTING.md`](docs/TESTING.md) for the full verification results.

---

## Privacy Architecture

| Rule | Implementation |
|---|---|
| Seeker never sees identity | The seeker receives only `filed` or `accepted` status. No name, photo, or contact until the recipient explicitly accepts and shares |
| Decline is silent | Declining a token updates `used=true` and `response="declined"`. The seeker's status stays `filed`. No "declined" message, no "seen" status |
| PII encrypted at rest | All memories, contacts, names, quiz answers, and messages encrypted with Fernet before storage |
| Originals never served | Verification images and group photos stored in `uploads/original/` — no route serves this directory. Only `uploads/redacted/` is reachable |
| Single-use tokens | 24-hour expiry. Reuse returns 410 Gone |
| Contact scrubbing | Chat messages are scanned for phone numbers, emails, and URLs. Matches return `400 contact_blocked` — the message is never stored |
| Payment-gated contact | The recipient's contact is only revealed after the seeker completes the $5.99 payment flow AND the recipient approves sharing |
| No public search | Matching is server-side only. There is no `/search` endpoint |
| Standard tier only | No `-contributor` model IDs — vulnerable people's data never trains a model |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI, SQLAlchemy, SQLite, Fernet (cryptography) |
| Frontend | React 18, Vite, Tailwind, react-router-dom, axios |
| AI Models | Muse Spark 1.3, Muse Wonder 1.0, SAM 3.1 via Meta Model API |
| Matching | rapidfuzz, jellyfish (Double Metaphone, Jaro-Winkler) |
| Dev tooling | Muse Code (agentic coding agent) |

---

## Running Locally

### Prerequisites

- Python 3.11+
- Node.js 18+
- A Meta Model API key (Standard tier)

### Setup

```bash
# Clone
git clone https://github.com/ayandipe/reunite.git
cd reunite

# Backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend && npm install && cd ..

# Environment
cp .env.example .env
# Edit .env and add your MODEL_API_KEY and FERNET_KEY

Generate a Fernet key
bash

python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

Paste the output into .env as FERNET_KEY=...
Run
bash

# Terminal A — backend
uvicorn backend.main:app --reload --port 8000

# Terminal B — frontend
cd frontend && npm run dev

Open http://localhost:5173
Health check
bash

curl http://localhost:8000/api/health
# {"ok":true,"service":"reunite"}

The Demo

Individual flow (recommended test):

    Open http://localhost:5173/

    Submit: "My sister Layla, near old market in Mosul, phone ended 4471, born 1988"

    Copy the request ID

    Open http://localhost:5173/admin → paste ID → Run match

    See: c1 at 0.85, traps at 0.65 and 0.575, resolved_by: muse_wonder, green VERIFIED line

    Click Issue consent token → copy the recipient link

    Open the recipient link → answer 71 → upload /tmp/ducks.jpg (or any image) → see SAM redaction

    Click Accept → open the secure channel

    Switch ?viewer=recipient to ?viewer=seeker → complete the $5.99 payment flow

    Recipient approves contact sharing → both can chat, contact scrubbing blocks phone numbers in messages

Group flow:

    Open http://localhost:5173/group

    Fill: context Mosul 2005 Methodist High School, names Layla, 5 quiz Q&As, phone 4471, birth year 1988

    Submit → confirmation shows "filed" + group ID

    Open http://localhost:5173/admin → paste group ID → Run group match

    Slots table shows Layla → c1 → 0.85 → Open recipient view →

    Click through to see the recipient's 5-question quiz

Silent decline test:

    Submit a new request → issue a token

    Open the recipient link → click Decline

    Back on the seeker's tab → click Refresh status → status stays filed

    Nothing happened. That's the privacy guarantee.

Testing

See docs/TESTING.md for:

    Encryption-at-rest verification

    Individual flow end-to-end tests (submit → match → verify → accept/decline)

    Group flow end-to-end tests (submit-group → match-group → quiz → accept)

    Silent decline proof (two paths, two outcomes)

    Contact scrubbing tests (phone/email/URL all blocked)

    Live model smoke test (Muse Spark, SAM 3.1, Muse Wonder all verified)

What Was Built During the Hackathon

Everything in this repository was written during the Meta Global AI Developer Hackathon (Oct 26 – Nov 4, 2026). The git history reflects daily commits from the first scaffold to the final demo.

Built with Muse Code, Meta's agentic coding tool. The .agents/AGENTS.md file at the repo root contains the project rules Muse Code reads at session start — model IDs, privacy constraints, and the source-of-truth hierarchy. The development trail is visible in the commit history and the docs/ folder.
Scope cuts (documented, not hidden)

    Real Meta SSO — the recipient's contact is a hardcoded placeholder (+234 ••• ••• 4471) with a note that in production it comes from Meta's identity layer

    Stripe / Meta Pay — the $5.99 payment is a UI mockup. The second modal explicitly says "For the hackathon demo, this step is simulated"

    WhatsApp Cloud API delivery — the recipient link is opened manually in the demo. Production delivery would use Meta's WhatsApp Business API with pre-approved templates, which requires business verification that cannot be completed in a weekend

    Photo perceptual hashing — cut from scope; kept the SAM 3.1 segmentation which is what the demo needs

    Group face clustering — SAM detects faces; Muse Spark maps names to slots. Automatic cross-photo face matching requires a face recognition model not in the hackathon toolchain. The seeker makes the final judgment by eye

Documentation

    AGENTS.md — project rules, model IDs, privacy constraints, current state

    docs/TESTING.md — full test runbook with verified results

    docs/DEMO_LINK.txt — 3-minute demo video

License

MIT — see LICENSE for details.
Acknowledgments

Built on Meta's AI infrastructure. Muse Spark, Muse Wonder, and SAM 3.1 were accessed via the Meta Model API. Muse Code was used as the agentic coding tool throughout the build.

The problem this solves is real. The families this could reconnect are real. If this prototype ever becomes something Meta ships, the goal is simple: consent, not search, opens the door.