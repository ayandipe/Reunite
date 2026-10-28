# backend/muse.py
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()

MUSE_MODE = os.getenv("MUSE_MODE", "mock")

def parse_memory(raw_text: str) -> dict:
    """Extract structured clues from a free-text memory."""
    if MUSE_MODE == "mock":
        return _mock_parse(raw_text)
    return _live_parse(raw_text)

def _mock_parse(raw_text: str) -> dict:
    # Keyword extraction for dev/testing — deterministic, no API calls.
    text = raw_text or ""

    birth_year = None
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if year_match:
        birth_year = int(year_match.group(1))

    phone_suffix = None
    year_text = year_match.group(1) if year_match else None
    phone_groups = [
        g for g in re.findall(r"\d{4,}", text) if g != year_text
    ]
    if phone_groups:
        phone_suffix = phone_groups[-1][-4:]

    hometown = None
    for known in ("Mosul", "Baghdad"):
        if re.search(r"\b" + known + r"\b", text, re.IGNORECASE):
            hometown = known
            break

    relationship = None
    rel_match = re.search(
        r"\b(sister|brother|mother|father|aunt|uncle|cousin|friend|"
        r"wife|husband|sibling)\b",
        text,
        re.IGNORECASE,
    )
    if rel_match:
        relationship = rel_match.group(1).lower()

    stop = {
        "my", "looking", "searching", "seeking", "find", "for",
        "in", "from", "near", "old", "market", "phone", "born", "ended",
        "sister", "brother", "mother", "father", "aunt", "uncle",
        "cousin", "friend", "wife", "husband", "sibling",
        "mosul", "baghdad",
    }
    name = None
    cue_match = re.search(
        r"(?:\bsister\b|\bbrother\b|\bmother\b|\bfather\b|\baunt\b|"
        r"\buncle\b|\bcousin\b|\bfriend\b|\bwife\b|\bhusband\b|"
        r"\bsibling\b|\blooking\s+for\b|\bsearching\s+for\b|"
        r"\bseeking\b|\bfind\b)\s+([A-Za-z]+)",
        text,
        re.IGNORECASE,
    )
    if cue_match:
        candidate = re.sub(r"[^A-Za-z]", "", cue_match.group(1))
        if candidate and candidate.lower() not in stop:
            name = candidate.capitalize()
    if name is None:
        for word in re.findall(r"\b([A-Z][a-z]+)\b", text):
            if word.lower() not in stop:
                name = word
                break

    return {
        "name": name,
        "relationship": relationship,
        "hometown": hometown,
        "phone_suffix": phone_suffix,
        "birth_year": birth_year,
        "confidence": 0.9 if name else 0.5,
    }

def _live_parse(raw_text: str) -> dict:
    from openai import OpenAI
    client = OpenAI(
        base_url="https://api.meta.ai/v1",
        api_key=os.environ["MODEL_API_KEY"],
    )
    resp = client.responses.create(
        model="muse-spark-1.3",
        input=(
            "Extract structured clues from this family-reconnection memory. "
            "Return STRICT JSON only with keys: name, relationship, hometown, "
            "phone_suffix, birth_year, confidence (0-1). No prose.\n\n"
            f"Memory: {raw_text}"
        ),
        reasoning={"effort": "medium"},
        max_output_tokens=8192,
    )
    text = resp.output_text.strip()
    # Strip code fences if the model wrapped it
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text)

def resolve_ambiguity(seeker: dict, top1: dict, top2: dict) -> str:
    """Return the candidate_id Muse Wonder picks. Mock picks top1; live calls the API."""
    if MUSE_MODE == "mock":
        return top1["candidate_id"]
    return _live_resolve(seeker, top1, top2)


def _live_resolve(seeker: dict, top1: dict, top2: dict) -> str:
    from openai import OpenAI
    client = OpenAI(base_url="https://api.meta.ai/v1", api_key=os.environ["MODEL_API_KEY"])
    prompt = (
        f"Seeker memory parsed: {seeker}\n"
        f"Candidate A: {top1}\n"
        f"Candidate B: {top2}\n"
        "Which candidate is more likely the same person? "
        "Answer with only 'A' or 'B'."
    )
    resp = client.responses.create(
        model="muse-wonder-1.0",
        input=prompt,
        reasoning={"effort": "high"},
        max_output_tokens=10,
    )
    answer = resp.output_text.strip().upper()
    return top1["candidate_id"] if answer.startswith("A") else top2["candidate_id"]