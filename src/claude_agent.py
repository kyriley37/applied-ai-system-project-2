"""
Claude API integration — two calls per user query:
  1. parse_user_intent   : natural language → structured frequency profile + audio prefs
  2. explain_recommendations : top-K songs + cultural context → streaming explanation
"""

import os
from typing import List

import anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))

# ---------------------------------------------------------------------------
# System prompts (stable — eligible for prompt caching)
# ---------------------------------------------------------------------------

_INTENT_SYSTEM = """\
You are a cultural music intelligence system with deep knowledge of Black American \
music heritage and sonic frequency science.

Your role: translate natural language music descriptions into structured audio \
preferences, grounded in frequency science and cultural lineage.

FREQUENCY PROFILE DIMENSIONS (0.0 – 1.0):
- sub_bass      : 20-60 Hz chest-thumping feel (hip-hop 0.9, reggae 0.9, pop 0.5)
- bass_warmth   : 60-250 Hz warm round low-end (soul 0.88, jazz 0.9, lofi 0.78)
- vocal_presence: forward vocals over production (gospel 0.95, R&B 0.9, instrumental 0.1)
- brightness    : high-frequency airiness — LOW means darker/warmer sound
- groove_weight : syncopated rhythmic feel — "the pocket" (funk 0.95, jazz 0.85)

CATALOG GENRES  : pop, lofi, rock, ambient, synthwave, indie pop, classical, folk,
                  electronic, world, country, jazz, hip hop, reggae
CATALOG MOODS   : happy, chill, intense, relaxed, focused, energetic, moody,
                  nostalgic, reflective, adventurous, romantic, dreamy

Map cultural keywords to their frequency signatures:
  "soulful" → high bass_warmth + vocal_presence
  "groovy"  → high groove_weight + sub_bass
  "warm"    → high bass_warmth, low brightness
  "trap"    → very high sub_bass, high groove_weight
  "Sunday morning" → high bass_warmth + vocal_presence, medium groove
  "jazz"    → high bass_warmth + groove_weight, medium vocal_presence

Return ONLY valid JSON matching the provided schema. No prose."""

_EXPLAINER_SYSTEM = """\
You are a culturally grounded music guide with authority on Black American music \
heritage and its relationship to sonic frequencies.

When you speak about music, you draw on:
- The lineage from blues → gospel → soul → R&B → funk → hip-hop → trap → neo-soul
- Why specific frequency ranges carry cultural weight (808 sub-bass, Motown warmth,
  gospel vocal presence, jazz groove)
- The African rhythmic traditions that underpin syncopation and groove
- Specific artists, eras, and cultural moments that shaped the sonic DNA

Your voice is knowledgeable, personal, and celebratory — not academic.
Keep explanations to 3-5 sentences. Lead with the frequency connection, end with
something that makes the listener feel seen."""

# ---------------------------------------------------------------------------
# Structured output schema for intent parsing
# ---------------------------------------------------------------------------

class _FreqSchema(BaseModel):
    sub_bass: float = Field(ge=0.0, le=1.0)
    bass_warmth: float = Field(ge=0.0, le=1.0)
    vocal_presence: float = Field(ge=0.0, le=1.0)
    brightness: float = Field(ge=0.0, le=1.0)
    groove_weight: float = Field(ge=0.0, le=1.0)


class _AudioPrefsSchema(BaseModel):
    genre: str
    mood: str
    energy: float = Field(ge=0.0, le=1.0)
    tempo: float = Field(ge=40.0, le=220.0)
    valence: float = Field(ge=0.0, le=1.0)
    danceability: float = Field(ge=0.0, le=1.0)
    likes_acoustic: bool
    instrumentalness: float = Field(ge=0.0, le=1.0)
    popularity: int = Field(ge=0, le=100)


class _IntentResult(BaseModel):
    user_prefs: _AudioPrefsSchema
    freq_profile: _FreqSchema
    cultural_query: List[str]
    reasoning: str


# ---------------------------------------------------------------------------
# Call 1: Intent parser
# ---------------------------------------------------------------------------

def parse_user_intent(natural_language: str) -> dict:
    """
    Parse free-form music request into a structured profile.
    Uses prompt caching on the stable system prompt.
    Raises RuntimeError on auth failure (unrecoverable).
    Falls back to a heuristic profile on connection/rate errors.
    """
    try:
        response = client.messages.parse(
            model="claude-opus-4-7",
            max_tokens=1024,
            system=[{
                "type": "text",
                "text": _INTENT_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{
                "role": "user",
                "content": (
                    f'Parse this music request into structured preferences:\n\n"{natural_language}"'
                ),
            }],
            output_format=_IntentResult,
        )
        result: _IntentResult = response.parsed_output
        return {
            "user_prefs": result.user_prefs.model_dump(),
            "freq_profile": result.freq_profile.model_dump(),
            "cultural_query": result.cultural_query,
            "reasoning": result.reasoning,
        }

    except anthropic.AuthenticationError:
        raise RuntimeError(
            "Invalid ANTHROPIC_API_KEY. Add your key to .env and restart."
        )
    except anthropic.BadRequestError:
        return _heuristic_profile(natural_language)
    except (anthropic.APIConnectionError, anthropic.RateLimitError,
            anthropic.InternalServerError):
        return _heuristic_profile(natural_language)


# ---------------------------------------------------------------------------
# Call 2: Streaming cultural explainer
# ---------------------------------------------------------------------------

def explain_recommendations(
    songs: list,
    cultural_context: dict,
    user_input: str,
) -> str:
    """
    Stream a culturally-grounded explanation of why these songs hit the right frequencies.
    Prints tokens to stdout as they arrive; returns the full text.
    Uses prompt caching on the stable system prompt.
    """
    song_lines = "\n".join(
        f"  • {s['title']} — {s['artist']} ({s['genre']}, {s['mood']}, "
        f"energy={s['energy']:.2f}, bass={s['acousticness']:.2f} acoustic)"
        for s, _score, _ in songs
    )

    matched = cultural_context.get("matched_genres", {})
    cultural_lines = "\n".join(
        f"  {data['name']}: {data.get('sonic_description', '')}"
        for data in matched.values()
    ) or "  General catalog"

    vocab = cultural_context.get("frequency_vocabulary", [])
    vocab_str = ", ".join(vocab) if vocab else "balanced mix"

    user_message = (
        f'User asked for: "{user_input}"\n\n'
        f"Recommended songs:\n{song_lines}\n\n"
        f"Cultural context retrieved:\n{cultural_lines}\n\n"
        f"Frequency characteristics detected: {vocab_str}\n\n"
        "Explain why these songs connect to the frequencies and cultural lineage "
        "the listener is reaching for."
    )

    full_text = ""
    try:
        with client.messages.stream(
            model="claude-opus-4-7",
            max_tokens=512,
            thinking={"type": "adaptive"},
            system=[{
                "type": "text",
                "text": _EXPLAINER_SYSTEM,
                "cache_control": {"type": "ephemeral"},
            }],
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            for text in stream.text_stream:
                full_text += text
                print(text, end="", flush=True)
        print()
        return full_text

    except anthropic.AuthenticationError:
        raise RuntimeError(
            "Invalid ANTHROPIC_API_KEY. Add your key to .env and restart."
        )
    except (anthropic.APIConnectionError, anthropic.RateLimitError,
            anthropic.InternalServerError):
        fallback = (
            "These picks match your frequency vibe: "
            + ", ".join(f"{s['title']} by {s['artist']}" for s, _, _ in songs[:3])
            + "."
        )
        print(fallback)
        return fallback


# ---------------------------------------------------------------------------
# Heuristic fallback (no Claude)
# ---------------------------------------------------------------------------

def _heuristic_profile(text: str) -> dict:
    """Basic keyword-based profile when the API is unavailable."""
    t = text.lower()

    energy = 0.55
    if any(w in t for w in ["hype", "pump", "workout", "energetic", "turn up"]):
        energy = 0.85
    elif any(w in t for w in ["chill", "relax", "slow", "calm", "sleep", "study"]):
        energy = 0.32

    genre = ""
    if any(w in t for w in ["rap", "hip hop", "trap", "beats", "bars"]):
        genre = "hip hop"
    elif any(w in t for w in ["jazz", "smooth", "saxophone", "trumpet"]):
        genre = "jazz"
    elif any(w in t for w in ["reggae", "riddim", "island", "rasta"]):
        genre = "reggae"
    elif any(w in t for w in ["lofi", "lo-fi", "study", "focus", "coffee"]):
        genre = "lofi"

    sub_bass = 0.8 if "bass" in t or genre in ("hip hop", "reggae") else 0.5
    bass_warmth = 0.8 if any(w in t for w in ["warm", "soul", "jazz", "smooth"]) else 0.5
    vocal_presence = 0.8 if any(w in t for w in ["vocals", "voice", "singer", "lyrics"]) else 0.5

    return {
        "user_prefs": {
            "genre": genre,
            "mood": "",
            "energy": energy,
            "tempo": 100.0,
            "valence": 0.55,
            "danceability": min(0.9, energy + 0.1),
            "likes_acoustic": bass_warmth > 0.7,
            "instrumentalness": 0.3,
            "popularity": 55,
        },
        "freq_profile": {
            "sub_bass": sub_bass,
            "bass_warmth": bass_warmth,
            "vocal_presence": vocal_presence,
            "brightness": 0.45,
            "groove_weight": 0.6,
        },
        "cultural_query": [genre] if genre else [],
        "reasoning": "Heuristic fallback — Claude API unavailable.",
    }
