# backend/matching.py
from rapidfuzz import fuzz
from jellyfish import jaro_winkler_similarity, metaphone
import re

THRESHOLD = 0.72
AMBIGUITY_GAP = 0.05


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower().strip())


def _phone_score(seeker_suffix: str, candidate_phone: str) -> float:
    if not seeker_suffix or not candidate_phone:
        return 0.0
    digits = re.sub(r"\D", "", candidate_phone)
    if not digits:
        return 0.0
    # Compare last 4 digits of candidate with seeker's remembered suffix
    tail = digits[-len(seeker_suffix):]
    return fuzz.ratio(seeker_suffix, tail) / 100.0


def _hometown_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return jaro_winkler_similarity(_norm(a), _norm(b))


def _name_score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return 1.0 if metaphone(_norm(a)) == metaphone(_norm(b)) else 0.0


def _year_score(seeker_year, candidate_year) -> float:
    if not seeker_year or not candidate_year:
        return 0.0
    diff = abs(int(seeker_year) - int(candidate_year))
    if diff <= 2:
        return 1.0
    if diff >= 8:
        return 0.0
    return 1.0 - (diff - 2) / 6.0


def _contact_overlap(seeker_contacts, candidate_contacts) -> float:
    if not seeker_contacts or not candidate_contacts:
        return 0.0
    s, c = set(seeker_contacts), set(candidate_contacts)
    union = s | c
    return len(s & c) / len(union) if union else 0.0


def score_candidate(seeker: dict, candidate: dict) -> dict:
    """Return score and per-feature breakdown. Deterministic, no LLM."""
    phone = _phone_score(seeker.get("phone_suffix"), candidate.get("phone", ""))
    hometown = _hometown_score(seeker.get("hometown"), candidate.get("hometown", ""))
    name = _name_score(seeker.get("name"), candidate.get("alias_name", ""))
    year = _year_score(seeker.get("birth_year"), candidate.get("birth_year"))
    contacts = _contact_overlap(seeker.get("contacts", []), candidate.get("known_contacts", []))

    total = (
        0.30 * phone +
        0.20 * hometown +
        0.20 * name +
        0.15 * year +
        0.10 * contacts
    )
    return {
        "score": round(total, 4),
        "breakdown": {
            "phone": round(phone, 4),
            "hometown": round(hometown, 4),
            "name": round(name, 4),
            "year": round(year, 4),
            "contacts": round(contacts, 4),
        },
    }


def rank_candidates(seeker: dict, candidates: list) -> list:
    scored = []
    for c in candidates:
        result = score_candidate(seeker, c)
        scored.append({"candidate_id": c["id"], **result})
    return sorted(scored, key=lambda x: x["score"], reverse=True)


def is_ambiguous(ranked: list) -> bool:
    if len(ranked) < 2:
        return False
    return abs(ranked[0]["score"] - ranked[1]["score"]) < AMBIGUITY_GAP


def threshold_met(score: float) -> bool:
    return score >= THRESHOLD