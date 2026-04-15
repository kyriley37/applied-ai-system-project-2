"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs


def main() -> None:
    songs = load_songs("data/songs.csv")
    print(f"Loaded songs: {len(songs)}")

    # Starter example profile
    user_prefs = {"genre": "pop", "mood": "happy", "energy": 0.8}

    print("\nUser Profile:")
    print(f"  Genre: {user_prefs['genre']}  |  Mood: {user_prefs['mood']}  |  Energy: {user_prefs['energy']}")
    print("\n" + "=" * 50)
    print("  Top Recommendations")
    print("=" * 50)

    recommendations = recommend_songs(user_prefs, songs, k=5)

    for rank, rec in enumerate(recommendations, start=1):
        song, score, explanation = rec
        print(f"\n#{rank}  {song['title']} by {song['artist']}")
        print(f"    Genre: {song['genre']}  |  Mood: {song['mood']}  |  Energy: {song['energy']:.2f}")
        print(f"    Score: {score:.2f} / 7.50")
        print(f"    Why:   {explanation.replace(' | ', chr(10) + '           ')}")
        print("-" * 50)


if __name__ == "__main__":
    main()
