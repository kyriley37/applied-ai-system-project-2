"""
Command line runner for the Cultural Frequency Music Recommender.

Usage:
  python -m src.main          # interactive mode (requires ANTHROPIC_API_KEY)
  python -m src.main --demo   # run pre-built demo profiles without the API
"""

import os
import argparse

from dotenv import load_dotenv
from tabulate import tabulate

from .recommender import load_songs, recommend_songs, diverse_recommend_songs, STRATEGIES

load_dotenv()


# ---------------------------------------------------------------------------
# Pre-built profiles
# ---------------------------------------------------------------------------

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
    "Ghost Genre (metal/angry)": {
        "genre": "metal",
        "mood": "angry",
        "energy": 0.95,
        "tempo": 160,
        "valence": 0.30,
        "danceability": 0.60,
        "likes_acoustic": False,
    },
    "High Energy + Chill Mood": {
        "genre": "lofi",
        "mood": "chill",
        "energy": 0.95,
        "tempo": 150,
        "valence": 0.50,
        "danceability": 0.50,
        "likes_acoustic": True,
    },
    "Acoustic Headbanger": {
        "genre": "rock",
        "mood": "intense",
        "energy": 0.95,
        "tempo": 155,
        "valence": 0.40,
        "danceability": 0.70,
        "likes_acoustic": True,
    },
    "No Genre No Mood (numeric only)": {
        "genre": "",
        "mood": "",
        "energy": 0.55,
        "tempo": 100,
        "valence": 0.65,
        "danceability": 0.65,
        "likes_acoustic": False,
    },
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


# ---------------------------------------------------------------------------
# Shared formatting helpers
# ---------------------------------------------------------------------------

def _wrap_reasons(explanation: str, max_reasons: int = 4, width: int = 38) -> str:
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


# ---------------------------------------------------------------------------
# Interactive mode — powered by Claude
# ---------------------------------------------------------------------------

def interactive_mode(songs: list) -> None:
    from .claude_agent import parse_user_intent, explain_recommendations
    from .cultural_retriever import load_kb, retrieve_cultural_context
    from .frequency_profile import freq_to_audio_prefs, freq_to_weights
    from .logger import setup_logger, log_api_call, log_retrieval, log_scoring, log_guardrail

    logger = setup_logger()
    kb = load_kb()

    print("\n" + "=" * 62)
    print("  Cultural Frequency Music Recommender")
    print("  Powered by Claude + Black American Music Heritage")
    print("=" * 62)
    print("\nDescribe what you want to hear in your own words.")
    print("Examples:")
    print('  "I want that deep bass Sunday morning soul feel"')
    print('  "Something groovy and funky for a late-night drive"')
    print('  "Chill jazzy vibes for studying, warm not bright"')
    print("\nType 'quit' to exit.\n")

    while True:
        try:
            user_input = input("What are you feeling? > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye.")
            break

        if len(user_input) > 500:
            print("Please keep your request under 500 characters.\n")
            log_guardrail(logger, "input_too_long", False)
            continue

        print("\nReading your vibe...", end="", flush=True)

        try:
            # Step 1: Parse intent via Claude (structured output)
            parsed = parse_user_intent(user_input)
            print(" done.\n")
            log_api_call(logger, "intent_parser", user_input, parsed.get("reasoning", ""))

            # Step 2: RAG — retrieve cultural context from knowledge base
            cultural_context = retrieve_cultural_context(
                parsed.get("cultural_query", []),
                parsed.get("freq_profile", {}),
                kb,
            )
            log_retrieval(logger, parsed.get("cultural_query", []), cultural_context)

            # Step 3: Map frequency profile → augmented audio prefs + custom weights
            merged_prefs = freq_to_audio_prefs(
                parsed.get("freq_profile", {}),
                parsed.get("user_prefs", {}),
            )
            freq_weights = freq_to_weights(parsed.get("freq_profile", {}))

            # Step 4: Score and rank songs
            results = recommend_songs(merged_prefs, songs, k=5, weights=freq_weights)
            log_scoring(logger, merged_prefs, results)

            # Step 5: Display ranked table
            print("Your frequencies:\n")
            rows = []
            for rank, (song, score, _explanation) in enumerate(results, start=1):
                rows.append([
                    f"#{rank}",
                    f"{song['title']}\n{song['artist']}",
                    f"{song['genre']}\n{song['mood']}",
                    f"{song['energy']:.2f}",
                    f"{score:.2f}",
                ])
            print(tabulate(
                rows,
                headers=["", "Title / Artist", "Genre / Mood", "Energy", "Score"],
                tablefmt="rounded_outline",
                colalign=("center", "left", "left", "center", "center"),
            ))

            # Step 6: Stream cultural explanation via Claude
            print()
            explanation = explain_recommendations(results, cultural_context, user_input)
            log_api_call(logger, "explainer", user_input[:100], explanation[:100])
            print()

        except RuntimeError as e:
            print(f"\nError: {e}")
            break

        except Exception as e:
            log_guardrail(logger, f"{type(e).__name__}: {e}", True)
            print(f"\nSomething went wrong ({type(e).__name__}). "
                  "Falling back to standard recommendations.\n")
            fallback = recommend_songs(
                {"energy": 0.5, "genre": "", "mood": ""}, songs, k=3
            )
            for rank, (song, _score, _) in enumerate(fallback, 1):
                print(f"  #{rank} {song['title']} — {song['artist']} ({song['genre']})")
            print()


# ---------------------------------------------------------------------------
# Demo mode
# ---------------------------------------------------------------------------

def demo_mode(songs: list) -> None:
    for label, prefs in PROFILES.items():
        print_recommendations(label, prefs, songs, k=3)

    print("\n\n*** ADVERSARIAL PROFILES ***")
    for label, prefs in ADVERSARIAL_PROFILES.items():
        print_recommendations(label, prefs, songs, k=5)

    comparison_profile = PROFILES["Chill Lofi"]
    print("\n\n*** STRATEGY COMPARISON — Chill Lofi profile ***")
    for strategy in STRATEGIES:
        print(f"\n--- Strategy: {strategy.upper()} ---")
        results = recommend_songs(comparison_profile, songs, k=3, strategy=strategy)
        for rank, (song, score, _) in enumerate(results, start=1):
            print(f"  #{rank}  {song['title']} ({song['genre']}, {song['mood']})  score={score:.2f}")

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


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Cultural Frequency Music Recommender")
    parser.add_argument("--demo", action="store_true",
                        help="Run pre-built demo profiles (no API key required)")
    args = parser.parse_args()

    songs = load_songs("data/songs.csv")
    print(f"Loaded {len(songs)} songs.")

    if args.demo:
        demo_mode(songs)
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("\nNo ANTHROPIC_API_KEY found in environment.")
        print("Add it to a .env file (see .env.example), then run again.")
        print("Running demo mode instead...\n")
        demo_mode(songs)
        return

    interactive_mode(songs)


if __name__ == "__main__":
    main()
