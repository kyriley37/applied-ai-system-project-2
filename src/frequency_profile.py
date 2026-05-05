from dataclasses import dataclass
from typing import Dict


@dataclass
class FrequencyProfile:
    """
    User's sonic frequency preferences (0.0 – 1.0 each).

    sub_bass      — 20-60 Hz: chest-thumping feel (hip-hop, trap, reggae)
    bass_warmth   — 60-250 Hz: warm, round low-end (soul, R&B, jazz)
    vocal_presence— forward vocals over production (gospel, neo-soul, R&B)
    brightness    — high-frequency content/airiness (low = darker/warmer)
    groove_weight — syncopated rhythmic feel, "the pocket" (funk, hip-hop, jazz)
    """
    sub_bass: float = 0.5
    bass_warmth: float = 0.5
    vocal_presence: float = 0.5
    brightness: float = 0.5
    groove_weight: float = 0.5

    @classmethod
    def from_dict(cls, d: dict) -> "FrequencyProfile":
        fields = cls.__dataclass_fields__
        return cls(**{k: float(v) for k, v in d.items() if k in fields})


def freq_to_audio_prefs(freq_profile: dict, base_prefs: dict) -> dict:
    """
    Augment base user_prefs dict with frequency profile mappings.
    Returns a new dict — does not mutate base_prefs.
    """
    prefs = dict(base_prefs)
    fp = FrequencyProfile.from_dict(freq_profile)

    # sub_bass → prefer low acousticness, high danceability + energy
    if fp.sub_bass > 0.6:
        prefs["likes_acoustic"] = False
        prefs["danceability"] = max(prefs.get("danceability", 0.5), fp.sub_bass * 0.95)
        prefs["energy"] = max(prefs.get("energy", 0.5), fp.sub_bass * 0.85)
        prefs["acousticness"] = min(prefs.get("acousticness", 0.5), 1.0 - fp.sub_bass)

    # bass_warmth → prefer moderate acousticness, richer lows
    if fp.bass_warmth > 0.65:
        current_acoustic = prefs.get("acousticness", 0.0)
        prefs["acousticness"] = max(current_acoustic, fp.bass_warmth * 0.55)

    # vocal_presence → prefer low instrumentalness (want vocals up front)
    if fp.vocal_presence > 0.5:
        prefs["instrumentalness"] = min(
            prefs.get("instrumentalness", 0.5),
            1.0 - fp.vocal_presence
        )

    # low brightness → prefer warmer/darker valence ceiling
    if fp.brightness < 0.4:
        prefs["valence"] = min(prefs.get("valence", 0.65), 0.72)

    # groove_weight → boost danceability, nudge tempo into rhythmic range
    if fp.groove_weight > 0.65:
        prefs["danceability"] = max(prefs.get("danceability", 0.5), fp.groove_weight * 0.9)
        if prefs.get("tempo", 100) < 75:
            prefs["tempo"] = max(prefs.get("tempo", 80), fp.groove_weight * 115)

    return prefs


def freq_to_weights(freq_profile: dict) -> dict:
    """
    Map frequency preferences to scoring engine weight overrides.
    Returns a blended weight dict based on the 'balanced' strategy.
    """
    from .recommender import STRATEGIES
    weights = dict(STRATEGIES["balanced"])
    fp = FrequencyProfile.from_dict(freq_profile)

    # sub_bass → amplify danceability and energy importance
    weights["danceability"] += fp.sub_bass * 2.0
    weights["energy"] += fp.sub_bass * 1.5

    # bass_warmth → amplify acousticness importance
    weights["acousticness"] += fp.bass_warmth * 1.2

    # vocal_presence → amplify instrumentalness proximity (penalise high instrumentalness)
    weights["instrumentalness"] += fp.vocal_presence * 1.5

    # groove_weight → amplify danceability and tempo importance
    weights["danceability"] += fp.groove_weight * 1.5
    weights["tempo"] += fp.groove_weight * 1.0

    # low brightness → liveness slightly more important (live = warmer feel)
    if fp.brightness < 0.5:
        weights["liveness"] += (0.5 - fp.brightness) * 0.6

    return weights
