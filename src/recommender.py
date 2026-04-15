from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

@dataclass
class Song:
    """A single song and its audio feature attributes."""
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float

@dataclass
class UserProfile:
    """A listener's taste preferences used to score and filter songs."""
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool

class Recommender:
    """OOP wrapper around the recommendation logic for a fixed song catalog."""
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"

def load_songs(csv_path: str) -> List[Dict]:
    """Read a CSV file of songs and return each row as a typed dictionary."""
    import csv
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            songs.append({
                "id":            int(row["id"]),
                "title":         row["title"],
                "artist":        row["artist"],
                "genre":         row["genre"],
                "mood":          row["mood"],
                "energy":        float(row["energy"]),
                "tempo_bpm":     float(row["tempo_bpm"]),
                "valence":       float(row["valence"]),
                "danceability":  float(row["danceability"]),
                "acousticness":  float(row["acousticness"]),
            })
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """Score a single song against user preferences and return (score, reasons)."""
    score = 0.0
    reasons = []

    # --- Categorical rules ---
    if song["genre"] == user_prefs.get("genre"):
        score += 2.0
        reasons.append(f"Matched your favorite genre ({song['genre']})")

    if song["mood"] == user_prefs.get("mood"):
        score += 1.0
        reasons.append(f"Matched your preferred mood ({song['mood']})")

    # --- Continuous similarity rules ---
    # Energy: tolerance ±0.40, max +1.5
    target_energy = user_prefs.get("energy", 0.5)
    energy_pts = max(0.0, 1 - abs(song["energy"] - target_energy) / 0.40) * 1.5
    if energy_pts > 0:
        score += energy_pts
        reasons.append(f"Energy close to your target ({song['energy']:.2f} vs {target_energy:.2f})")

    # Tempo: tolerance ±40 BPM, max +1.0
    target_tempo = user_prefs.get("tempo", 100.0)
    tempo_pts = max(0.0, 1 - abs(song["tempo_bpm"] - target_tempo) / 40.0) * 1.0
    if tempo_pts > 0:
        score += tempo_pts
        reasons.append(f"Tempo close to your target ({song['tempo_bpm']:.0f} BPM vs {target_tempo:.0f} BPM)")

    # Valence: tolerance ±0.30, max +0.75
    target_valence = user_prefs.get("valence", 0.5)
    valence_pts = max(0.0, 1 - abs(song["valence"] - target_valence) / 0.30) * 0.75
    if valence_pts > 0:
        score += valence_pts
        reasons.append(f"Valence close to your target ({song['valence']:.2f} vs {target_valence:.2f})")

    # Danceability: tolerance ±0.30, max +0.75
    target_dance = user_prefs.get("danceability", 0.5)
    dance_pts = max(0.0, 1 - abs(song["danceability"] - target_dance) / 0.30) * 0.75
    if dance_pts > 0:
        score += dance_pts
        reasons.append(f"Danceability close to your target ({song['danceability']:.2f} vs {target_dance:.2f})")

    # --- Acousticness preference rule ---
    likes_acoustic = user_prefs.get("likes_acoustic", False)
    if likes_acoustic and song["acousticness"] > 0.6:
        score += 0.5
        reasons.append("Acoustic track matches your preference")
    elif not likes_acoustic and song["acousticness"] < 0.3:
        score += 0.5
        reasons.append("Non-acoustic track matches your preference")

    return (score, reasons)

def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """Score all songs, sort by score descending, and return the top k as (song, score, explanation)."""
    scored = [
        (song, score, " | ".join(reasons) or "No strong matches")
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    ]
    return sorted(scored, key=lambda x: x[1], reverse=True)[:k]
