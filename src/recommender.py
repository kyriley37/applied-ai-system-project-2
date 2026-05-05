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
        prefs = {
            "genre": user.favorite_genre,
            "mood": user.favorite_mood,
            "energy": user.target_energy,
            "likes_acoustic": user.likes_acoustic,
        }
        raw_songs = [s.__dict__ for s in self.songs]
        results = recommend_songs(prefs, raw_songs, k=k)
        ids = {s["id"] for s, _, _ in results}
        return [s for s in self.songs if s.id in ids][:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        reasons = []
        if song.genre == user.favorite_genre:
            reasons.append(f"matches your favourite genre ({song.genre})")
        if song.mood == user.favorite_mood:
            reasons.append(f"fits your preferred mood ({song.mood})")
        energy_diff = abs(song.energy - user.target_energy)
        if energy_diff <= 0.2:
            reasons.append(f"energy level is close to your target ({song.energy:.2f})")
        if user.likes_acoustic and song.acousticness > 0.6:
            reasons.append("has the acoustic quality you enjoy")
        if not reasons:
            return f"'{song.title}' was selected based on overall audio feature match."
        return f"'{song.title}' by {song.artist} was recommended because it {', '.join(reasons)}."

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
                "popularity":        int(row["popularity"]),
                "release_decade":    int(row["release_decade"]),
                "mood_tag":          row["mood_tag"],
                "liveness":          float(row["liveness"]),
                "instrumentalness":  float(row["instrumentalness"]),
            })
    return songs

# ---------------------------------------------------------------------------
# Ranking strategies — each dict overrides the default feature weights.
# "balanced" reflects the original tuned recipe.
# Pass a strategy name to recommend_songs() to switch modes.
# ---------------------------------------------------------------------------
STRATEGIES: Dict[str, Dict[str, float]] = {
    "balanced": {
        "genre": 1.0, "mood": 1.0, "mood_tag": 1.5,
        "energy": 3.0, "tempo": 1.0, "valence": 0.75, "danceability": 0.75,
        "acousticness": 0.5, "popularity": 1.0, "decade_exact": 0.75,
        "decade_near": 0.25, "liveness": 0.5, "instrumentalness": 0.75,
    },
    "genre-first": {
        # Genre dominates everything; numeric features act as tiebreakers only
        "genre": 4.0, "mood": 0.5, "mood_tag": 0.5,
        "energy": 1.0, "tempo": 0.5, "valence": 0.25, "danceability": 0.25,
        "acousticness": 0.25, "popularity": 0.5, "decade_exact": 0.25,
        "decade_near": 0.1, "liveness": 0.25, "instrumentalness": 0.25,
    },
    "mood-first": {
        # Emotional feel matters most; genre is a weak signal
        "genre": 0.5, "mood": 3.0, "mood_tag": 3.0,
        "energy": 1.5, "tempo": 0.5, "valence": 1.0, "danceability": 0.5,
        "acousticness": 0.25, "popularity": 0.5, "decade_exact": 0.25,
        "decade_near": 0.1, "liveness": 0.25, "instrumentalness": 0.5,
    },
    "energy-focused": {
        # Rhythmic and intensity features drive ranking; labels barely count
        "genre": 0.25, "mood": 0.25, "mood_tag": 0.25,
        "energy": 6.0, "tempo": 2.0, "valence": 1.0, "danceability": 1.5,
        "acousticness": 0.5, "popularity": 0.25, "decade_exact": 0.1,
        "decade_near": 0.05, "liveness": 0.25, "instrumentalness": 0.25,
    },
}


def score_song(user_prefs: Dict, song: Dict, weights: Optional[Dict] = None) -> Tuple[float, List[str]]:
    """Score a single song against user preferences and return (score, reasons)."""
    w = weights or STRATEGIES["balanced"]
    score = 0.0
    reasons = []

    # --- Categorical rules ---
    if song["genre"] == user_prefs.get("genre"):
        score += w["genre"]
        reasons.append(f"Matched your favorite genre ({song['genre']})")

    if song["mood"] == user_prefs.get("mood"):
        score += w["mood"]
        reasons.append(f"Matched your preferred mood ({song['mood']})")

    # --- Continuous similarity rules ---
    # Energy: tolerance ±0.40
    target_energy = user_prefs.get("energy", 0.5)
    energy_pts = max(0.0, 1 - abs(song["energy"] - target_energy) / 0.40) * w["energy"]
    if energy_pts > 0:
        score += energy_pts
        reasons.append(f"Energy close to your target ({song['energy']:.2f} vs {target_energy:.2f})")

    # Tempo: tolerance ±40 BPM
    target_tempo = user_prefs.get("tempo", 100.0)
    tempo_pts = max(0.0, 1 - abs(song["tempo_bpm"] - target_tempo) / 40.0) * w["tempo"]
    if tempo_pts > 0:
        score += tempo_pts
        reasons.append(f"Tempo close to your target ({song['tempo_bpm']:.0f} BPM vs {target_tempo:.0f} BPM)")

    # Valence: tolerance ±0.30
    target_valence = user_prefs.get("valence", 0.5)
    valence_pts = max(0.0, 1 - abs(song["valence"] - target_valence) / 0.30) * w["valence"]
    if valence_pts > 0:
        score += valence_pts
        reasons.append(f"Valence close to your target ({song['valence']:.2f} vs {target_valence:.2f})")

    # Danceability: tolerance ±0.30
    target_dance = user_prefs.get("danceability", 0.5)
    dance_pts = max(0.0, 1 - abs(song["danceability"] - target_dance) / 0.30) * w["danceability"]
    if dance_pts > 0:
        score += dance_pts
        reasons.append(f"Danceability close to your target ({song['danceability']:.2f} vs {target_dance:.2f})")

    # --- Acousticness preference rule ---
    likes_acoustic = user_prefs.get("likes_acoustic", False)
    if likes_acoustic and song["acousticness"] > 0.6:
        score += w["acousticness"]
        reasons.append("Acoustic track matches your preference")
    elif not likes_acoustic and song["acousticness"] < 0.3:
        score += w["acousticness"]
        reasons.append("Non-acoustic track matches your preference")

    # --- Advanced feature rules ---
    if song["mood_tag"] == user_prefs.get("mood_tag"):
        score += w["mood_tag"]
        reasons.append(f"Mood tag matched ({song['mood_tag']})")

    # Popularity proximity: tolerance ±50
    target_popularity = user_prefs.get("popularity", 50)
    pop_pts = max(0.0, 1 - abs(song["popularity"] - target_popularity) / 50.0) * w["popularity"]
    if pop_pts > 0:
        score += pop_pts
        reasons.append(f"Popularity close to your target ({song['popularity']} vs {target_popularity})")

    # Release decade: exact or one-decade-off
    target_decade = user_prefs.get("release_decade")
    if target_decade is not None:
        decade_diff = abs(song["release_decade"] - target_decade)
        if decade_diff == 0:
            score += w["decade_exact"]
            reasons.append(f"Released in your preferred decade ({song['release_decade']}s)")
        elif decade_diff <= 10:
            score += w["decade_near"]
            reasons.append(f"Released close to your preferred decade ({song['release_decade']}s)")

    # Liveness proximity: tolerance ±0.5
    target_liveness = user_prefs.get("liveness", 0.2)
    live_pts = max(0.0, 1 - abs(song["liveness"] - target_liveness) / 0.5) * w["liveness"]
    if live_pts > 0:
        score += live_pts
        reasons.append(f"Liveness close to your target ({song['liveness']:.2f} vs {target_liveness:.2f})")

    # Instrumentalness proximity: tolerance ±0.5
    target_instrumental = user_prefs.get("instrumentalness", 0.5)
    inst_pts = max(0.0, 1 - abs(song["instrumentalness"] - target_instrumental) / 0.5) * w["instrumentalness"]
    if inst_pts > 0:
        score += inst_pts
        reasons.append(f"Instrumentalness close to your target ({song['instrumentalness']:.2f} vs {target_instrumental:.2f})")

    return (score, reasons)


def recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: str = "balanced",
    weights: Optional[Dict] = None,
) -> List[Tuple[Dict, float, str]]:
    """Score all songs and return the top k as (song, score, explanation).

    Pass ``weights`` to override the strategy lookup entirely — used by the
    frequency-profile mapper to inject custom scoring weights.
    """
    w = weights if weights is not None else STRATEGIES.get(strategy, STRATEGIES["balanced"])
    scored = [
        (song, score, " | ".join(reasons) or "No strong matches")
        for song in songs
        for score, reasons in [score_song(user_prefs, song, w)]
    ]
    return sorted(scored, key=lambda x: x[1], reverse=True)[:k]


def diverse_recommend_songs(
    user_prefs: Dict,
    songs: List[Dict],
    k: int = 5,
    strategy: str = "balanced",
    artist_penalty: float = 2.0,
    genre_penalty: float = 1.0,
) -> List[Tuple[Dict, float, float, str]]:
    """
    Greedy diversity-aware recommendation.

    Scores all songs first, then selects k songs one at a time.
    Each time a song is picked, any remaining song sharing its artist
    loses artist_penalty points and any sharing its genre loses
    genre_penalty points from their effective score for the next pick.
    Ties in effective score are broken by the original raw score.

    Returns (song, raw_score, effective_score, explanation) tuples.
    """
    weights = STRATEGIES.get(strategy, STRATEGIES["balanced"])

    # Step 1 — score every song once
    candidates = [
        (song, score, " | ".join(reasons) or "No strong matches")
        for song in songs
        for score, reasons in [score_song(user_prefs, song, weights)]
    ]

    selected = []
    seen_artists: Dict[str, int] = {}  # artist -> times already selected
    seen_genres: Dict[str, int] = {}   # genre  -> times already selected

    # Step 2 — greedy pick loop
    while len(selected) < k and candidates:
        # Apply diversity penalties to get each candidate's effective score
        def effective(entry):
            song, raw, _ = entry
            penalty = (seen_artists.get(song["artist"], 0) * artist_penalty
                       + seen_genres.get(song["genre"], 0) * genre_penalty)
            return raw - penalty

        best = max(candidates, key=effective)
        song, raw_score, explanation = best

        eff_score = effective(best)
        selected.append((song, raw_score, eff_score, explanation))
        candidates.remove(best)

        # Update penalty trackers
        seen_artists[song["artist"]] = seen_artists.get(song["artist"], 0) + 1
        seen_genres[song["genre"]]   = seen_genres.get(song["genre"], 0) + 1

    return selected
