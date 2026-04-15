"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from tabulate import tabulate
from .recommender import load_songs, recommend_songs, diverse_recommend_songs, STRATEGIES


PROFILES = {
    "High-Energy Pop": {
        "genre": "pop",
        "mood": "happy",
        "energy": 0.88,
        "tempo": 125,
        "valence": 0.80,
        "danceability": 0.85,
        "likes_acoustic": False,
    },
    "Chill Lofi": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.38,
        "tempo": 78,
        "valence": 0.58,
        "danceability": 0.60,
        "likes_acoustic": True,
    },
    "Deep Intense Rock": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.92,
        "tempo": 148,
        "valence": 0.45,
        "danceability": 0.65,
        "likes_acoustic": False,
    },
    "Late Night Jazz": {
        "genre": "jazz",
        "mood": "relaxed",
        "energy": 0.35,
        "tempo": 88,
        "valence": 0.68,
        "danceability": 0.52,
        "likes_acoustic": True,
    },
}


ADVERSARIAL_PROFILES = {
    # Genre that does not exist in the catalog — +2.0 never fires
    "Ghost Genre (metal/angry)": {
        "genre": "metal",
        "mood": "angry",
        "energy": 0.95,
        "tempo": 160,
        "valence": 0.30,
        "danceability": 0.60,
        "likes_acoustic": False,
    },
    # Mood says slow/chill, energy says maximum intensity — internal contradiction
    "High Energy + Chill Mood": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.95,
        "tempo": 150,
        "valence": 0.50,
        "danceability": 0.50,
        "likes_acoustic": True,
    },
    # likes_acoustic=True but energy/tempo target loud rock — acoustic tracks are low-energy
    "Acoustic Headbanger": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.95,
        "tempo": 155,
        "valence": 0.40,
        "danceability": 0.70,
        "likes_acoustic": True,
    },
    # No genre or mood — pure numeric scoring, no categorical boosts possible
    "No Genre No Mood (numeric only)": {
        "genre": "",
        "mood": "",
        "energy": 0.55,
        "tempo": 100,
        "valence": 0.65,
        "danceability": 0.65,
        "likes_acoustic": False,
    },
    # All targets at extreme 0.0 — tests the floor of the scoring formula
    "Extreme Low (everything 0)": {
        "genre": "ambient",
        "mood": "chill",
        "energy": 0.0,
        "tempo": 0,
        "valence": 0.0,
        "danceability": 0.0,
        "likes_acoustic": True,
    },
}


def _wrap_reasons(explanation: str, max_reasons: int = 4, width: int = 38) -> str:
    """Format pipe-separated reasons as a numbered list, capped at max_reasons."""
    import textwrap
    reasons = explanation.split(" | ")[:max_reasons]
    lines = []
    for i, r in enumerate(reasons, start=1):
        wrapped = textwrap.fill(r, width=width, subsequent_indent="   ")
        lines.append(f"{i}. {wrapped}")
    if len(explanation.split(" | ")) > max_reasons:
        lines.append("   ...")
    return "\n".join(lines)


def print_recommendations(label: str, user_prefs: dict, songs: list, k: int = 3) -> None:
    genre = user_prefs.get("genre") or "(none)"
    mood  = user_prefs.get("mood")  or "(none)"

    print(f"\n{'=' * 72}")
    print(f"  Profile : {label}")
    print(f"  Genre   : {genre}   Mood: {mood}   Energy: {user_prefs['energy']}")
    print(f"{'=' * 72}")

    rows = []
    for rank, (song, score, explanation) in enumerate(
        recommend_songs(user_prefs, songs, k=k), start=1
    ):
        rows.append([
            f"#{rank}",
            f"{song['title']}\n{song['artist']}",
            f"{song['genre']}\n{song['mood']}",
            f"{song['energy']:.2f}",
            f"{score:.2f}/12.5",
            _wrap_reasons(explanation),
        ])

    print(tabulate(
        rows,
        headers=["", "Title / Artist", "Genre / Mood", "Energy", "Score", "Why"],
        tablefmt="rounded_outline",
        colalign=("center", "left", "left", "center", "center", "left"),
    ))


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    for label, prefs in PROFILES.items():
        print_recommendations(label, prefs, songs, k=3)

    print("\n\n*** ADVERSARIAL PROFILES ***")
    for label, prefs in ADVERSARIAL_PROFILES.items():
        print_recommendations(label, prefs, songs, k=5)

    # --- Strategy comparison ---
    comparison_profile = PROFILES["Chill Lofi"]
    print("\n\n*** STRATEGY COMPARISON — Chill Lofi profile ***")
    for strategy in STRATEGIES:
        print(f"\n--- Strategy: {strategy.upper()} ---")
        results = recommend_songs(comparison_profile, songs, k=3, strategy=strategy)
        for rank, (song, score, _) in enumerate(results, start=1):
            print(f"  #{rank}  {song['title']} ({song['genre']}, {song['mood']})  score={score:.2f}")

    # --- Diversity penalty comparison ---
    print(f"\n\n{'=' * 72}")
    print("  DIVERSITY PENALTY — Chill Lofi profile")
    print(f"{'=' * 72}")

    std_rows = [
        [f"#{r}", f"{s['title']}\n{s['artist']}", s["genre"], f"{sc:.2f}",
         _wrap_reasons(ex)]
        for r, (s, sc, ex) in enumerate(
            recommend_songs(comparison_profile, songs, k=5), start=1)
    ]
    print("\nStandard (no penalty):")
    print(tabulate(std_rows,
                   headers=["", "Title / Artist", "Genre", "Score", "Why"],
                   tablefmt="rounded_outline",
                   colalign=("center", "left", "left", "center", "left")))

    div_rows = [
        [f"#{r}", f"{s['title']}\n{s['artist']}", s["genre"],
         f"{raw:.2f}", f"{eff:.2f}",
         f"-{raw - eff:.1f}" if raw - eff > 0 else "—",
         _wrap_reasons(ex)]
        for r, (s, raw, eff, ex) in enumerate(
            diverse_recommend_songs(comparison_profile, songs, k=5), start=1)
    ]
    print("\nDiverse (artist penalty -2.0 | genre penalty -1.0):")
    print(tabulate(div_rows,
                   headers=["", "Title / Artist", "Genre", "Raw", "Eff", "Penalty", "Why"],
                   tablefmt="rounded_outline",
                   colalign=("center", "left", "left", "center", "center", "center", "left")))


if __name__ == "__main__":
    main()
