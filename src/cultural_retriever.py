import json
from pathlib import Path
from typing import Dict, List


def load_kb(kb_path: str = "data/cultural_kb.json") -> dict:
    with open(kb_path, encoding="utf-8") as f:
        return json.load(f)


def retrieve_cultural_context(
    query_genres: List[str],
    freq_profile: dict,
    kb: dict,
) -> dict:
    """
    RAG retrieval: match the user's intent against the cultural knowledge base.

    Matches genres by:
      1. Direct catalog tag overlap with query_genres
      2. Dominant frequency dimension (e.g. high sub_bass → hip-hop, reggae)

    Returns matched genre entries + frequency vocabulary terms.
    """
    matched: Dict[str, dict] = {}

    # Pass 1: catalog tag match
    normalised_query = [g.lower().strip() for g in query_genres]
    for genre_key, genre_data in kb.get("genres", {}).items():
        tags = [t.lower() for t in genre_data.get("catalog_tags", [])]
        if any(tag in normalised_query for tag in tags) or genre_key in normalised_query:
            matched[genre_key] = genre_data

    # Pass 2: frequency profile match
    dominant = _dominant_freq_dim(freq_profile)
    for genre_key, genre_data in kb.get("genres", {}).items():
        if genre_key in matched:
            continue
        freq_sig = genre_data.get("frequency_signature", {})
        if freq_sig.get(dominant, 0) >= 0.75:
            matched[genre_key] = genre_data

    # Pass 3: keyword match against query_genres (covers "soul", "funk", etc.)
    for genre_key, genre_data in kb.get("genres", {}).items():
        if genre_key in matched:
            continue
        kws = [k.lower() for k in genre_data.get("keywords", [])]
        if any(q in kws for q in normalised_query):
            matched[genre_key] = genre_data

    vocab = _match_freq_vocabulary(freq_profile, kb)

    return {
        "matched_genres": matched,
        "frequency_vocabulary": vocab,
    }


def _dominant_freq_dim(freq_profile: dict) -> str:
    if not freq_profile:
        return "bass_warmth"
    return max(freq_profile, key=lambda k: float(freq_profile.get(k, 0)))


def _match_freq_vocabulary(freq_profile: dict, kb: dict) -> List[str]:
    """Return vocabulary terms whose frequency signatures overlap with the profile."""
    vocab = kb.get("frequency_vocabulary", {})
    matches = []
    for term, freq_vals in vocab.items():
        if not freq_vals:
            continue
        score = sum(
            min(float(freq_profile.get(dim, 0)), float(val))
            for dim, val in freq_vals.items()
        ) / len(freq_vals)
        if score >= 0.55:
            matches.append(term)
    return matches
