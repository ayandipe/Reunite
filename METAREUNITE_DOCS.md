# MetaReunite — Pre-Build Documentation
# Version 2.0 | Verified Meta AI Tooling Reference
# Read this BEFORE writing the first line of code.

---

## QUICK REFERENCE CARD

| Tool | Model ID | Endpoint | Job in MetaReunite | Critical Gotcha |
|------|----------|----------|-------------------|-----------------|
| Muse Spark | `muse-spark-1.3` | `/v1/responses` | Parse messy memories → structured JSON | Use Standard tier (no `-contributor`) |
| Muse Wonder | `muse-wonder-1.0` | `/v1/responses` | Resolve ambiguous matches | Full is NOT on API — only in Muse Code subscription |
| SAM 3.1 | `sam-3.1` | `/v1/responses` | Redact faces/IDs from verification images | Prompt must be SHORT NOUN PHRASE, one concept per call |
| Muse Image | `muse-image-1.0` | `/v1/responses` | Hero image, icons | Use `client.images.generate` / `client.images.edit` |
| Muse Code | CLI | Terminal | Build the entire project | `irm https://dev.meta.ai/install.ps1 \| iex` (Windows) |

**Base URL:** `https://api.meta.ai/v1`
**Auth Header:** `Authorization: Bearer $MODEL_API_KEY`

---

## 1. PROJECT IDENTITY

**Name:** MetaReunite
**Category:** Indie
**Tagline:** A privacy-first, consensual platform using Meta's AI to safely reconnect families separated by war, migration, and crisis.

**The Problem:**
Millions of families are displaced every year by war and crisis. They search for each other chaotically on social platforms, exposed to bad actors and tracking. There is no secure, consent-first framework to turn a desperate search into a safe connection.

**The Solution:**
A "Blind Notification Bridge." A seeker files a confidential request with historical identifiers. Meta's AI models match it against profiles in the background. The person being sought receives a private, redacted request and chooses to accept or decline. The seeker NEVER sees who was found unless the sought person explicitly consents. Decline is silent.

**Why Meta:**
Meta already has the social graph and the AI models. MetaReunite is an integration and policy layer on top of existing infrastructure. It embodies Meta's mission to "bring the world closer together" in its purest form.

---

## 2. JUDGING CRITERIA MAPPING

| Criterion | Weight | How We Win It |
|-----------|--------|---------------|
| Impact | 30% | Real humanitarian problem, authentic personal framing, safety-first design, directly usable. |
| Use of Meta AI Tooling | 25% | THREE model families for THREE distinct jobs: Muse Spark (parsing), Muse Wonder (reasoning), SAM 3.1 (redaction), all orchestrated with Muse Code. Deep, not surface. |
| Technical Depth & Execution | 20% | Real fuzzy-matching engine, Fernet encryption at rest, signed one-time tokens, provable privacy via SAM masks, agentic build with Muse Code `/plan` and `/grill`. |
| Demo | 25% | Live SAM redaction + live "silent rejection" proof. Working end-to-end loop. Pre-recorded backup video. |

---

## 3. ENVIRONMENT SETUP (DO THIS BEFORE DAY 1)

### 3.1 Install Python dependencies
```bash
pip install fastapi uvicorn sqlalchemy cryptography rapidfuzz jellyfish python-multipart httpx pillow python-dotenv openai