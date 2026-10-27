# backend/muse.py
import os
import json
from dotenv import load_dotenv

load_dotenv()

MUSE_MODE = os.getenv("MUSE_MODE", "mock")

def parse_memory(raw_text: str) -> dict:
    """Extract structured clues from a free-text memory."""
    if MUSE_MODE == "mock":
        return _mock_parse(raw_text)
    return _live_parse(raw_text)

def _mock_parse(raw_text: str) -> dict:
    # Deterministic output for dev/testing — swap for _live_parse in demo
    return {
        "name": "Layla",
        "relationship": "sister",
        "hometown": "Mosul",
        "phone_suffix": "4471",
        "birth_year": 1988,
        "confidence": 0.9,
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