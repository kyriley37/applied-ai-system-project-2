"""
Reliability and consistency test harness for the Cultural Frequency Music Recommender.

Tests run against the real songs.csv catalog (no mocking) to verify:
  - Consistency   : same profile always yields the same top-3 songs
  - Precision     : top result genre matches the dominant profile genre
  - Coverage      : all four strategies return k results
  - Diversity     : diverse_recommend_songs selects songs from multiple genres
  - Edge cases    : ghost genres, empty labels, extreme numeric values
  - Frequency map : freq_to_audio_prefs and freq_to_weights produce valid outputs
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.recommender import load_songs, recommend_songs, diverse_recommend_songs, STRATEGIES
from src.frequency_profile import freq_to_audio_prefs, freq_to_weights

SONGS = load_songs("data/songs.csv")

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def songs():
    return SONGS


@pytest.fixture
def pop_profile():
    return {
        "genre": "pop", "mood": "happy",
        "energy": 0.88, "tempo": 125,
        "valence": 0.80, "danceability": 0.85,
        "likes_acoustic": False,
    }


@pytest.fixture
def lofi_profile():
    return {
        "genre": "lofi", "mood": "chill",
        "energy": 0.38, "tempo": 78,
        "valence": 0.58, "danceability": 0.60,
        "likes_acoustic": True,
    }


@pytest.fixture
def jazz_profile():
    return {
        "genre": "jazz", "mood": "relaxed",
        "energy": 0.35, "tempo": 88,
        "valence": 0.68, "danceability": 0.52,
        "likes_acoustic": True,
    }


# ---------------------------------------------------------------------------
# Consistency — deterministic output
# ---------------------------------------------------------------------------

class TestConsistency:
    def test_same_profile_same_top3_pop(self, songs, pop_profile):
        run1 = [s["title"] for s, _, _ in recommend_songs(pop_profile, songs, k=3)]
        run2 = [s["title"] for s, _, _ in recommend_songs(pop_profile, songs, k=3)]
        assert run1 == run2, "Top-3 results are not deterministic for pop profile"

    def test_same_profile_same_top3_lofi(self, songs, lofi_profile):
        run1 = [s["title"] for s, _, _ in recommend_songs(lofi_profile, songs, k=3)]
        run2 = [s["title"] for s, _, _ in recommend_songs(lofi_profile, songs, k=3)]
        assert run1 == run2, "Top-3 results are not deterministic for lofi profile"

    def test_same_profile_same_top3_jazz(self, songs, jazz_profile):
        run1 = [s["title"] for s, _, _ in recommend_songs(jazz_profile, songs, k=3)]
        run2 = [s["title"] for s, _, _ in recommend_songs(jazz_profile, songs, k=3)]
        assert run1 == run2, "Top-3 results are not deterministic for jazz profile"


# ---------------------------------------------------------------------------
# Precision — top result relevance
# ---------------------------------------------------------------------------

class TestPrecision:
    def test_top_result_is_pop_for_pop_profile(self, songs, pop_profile):
        results = recommend_songs(pop_profile, songs, k=5)
        top_genre = results[0][0]["genre"]
        assert top_genre == "pop", f"Expected pop as top result, got {top_genre}"

    def test_top_result_is_lofi_for_lofi_profile(self, songs, lofi_profile):
        results = recommend_songs(lofi_profile, songs, k=5)
        top_genre = results[0][0]["genre"]
        assert top_genre == "lofi", f"Expected lofi as top result, got {top_genre}"

    def test_top_result_is_jazz_for_jazz_profile(self, songs, jazz_profile):
        results = recommend_songs(jazz_profile, songs, k=5)
        top_genre = results[0][0]["genre"]
        assert top_genre == "jazz", f"Expected jazz as top result, got {top_genre}"

    def test_scores_are_descending(self, songs, pop_profile):
        results = recommend_songs(pop_profile, songs, k=5)
        scores = [score for _, score, _ in results]
        assert scores == sorted(scores, reverse=True), "Scores are not in descending order"


# ---------------------------------------------------------------------------
# Strategy coverage — all four strategies return valid results
# ---------------------------------------------------------------------------

class TestStrategyCoverage:
    @pytest.mark.parametrize("strategy", list(STRATEGIES.keys()))
    def test_strategy_returns_k_results(self, songs, lofi_profile, strategy):
        results = recommend_songs(lofi_profile, songs, k=3, strategy=strategy)
        assert len(results) == 3, f"Strategy '{strategy}' returned {len(results)} results, expected 3"

    @pytest.mark.parametrize("strategy", list(STRATEGIES.keys()))
    def test_strategy_scores_are_non_negative(self, songs, lofi_profile, strategy):
        results = recommend_songs(lofi_profile, songs, k=3, strategy=strategy)
        for song, score, _ in results:
            assert score >= 0, f"Negative score {score} for '{song['title']}' with strategy '{strategy}'"

    def test_genre_first_strategy_boosts_genre_match(self, songs, jazz_profile):
        genre_first = recommend_songs(jazz_profile, songs, k=1, strategy="genre-first")
        balanced    = recommend_songs(jazz_profile, songs, k=1, strategy="balanced")
        assert genre_first[0][0]["genre"] == "jazz", "genre-first should return jazz song for jazz profile"
        assert balanced[0][0]["genre"] == "jazz", "balanced should also return jazz song for jazz profile"


# ---------------------------------------------------------------------------
# Diversity — diverse_recommend_songs spreads across genres/artists
# ---------------------------------------------------------------------------

class TestDiversity:
    def test_diverse_returns_k_results(self, songs, lofi_profile):
        results = diverse_recommend_songs(lofi_profile, songs, k=5)
        assert len(results) == 5

    def test_diverse_result_structure(self, songs, lofi_profile):
        results = diverse_recommend_songs(lofi_profile, songs, k=3)
        for song, raw, eff, explanation in results:
            assert isinstance(song, dict)
            assert raw >= eff, "Effective score should be <= raw score (penalty applied)"
            assert isinstance(explanation, str)

    def test_diverse_penalises_repeated_genre(self, songs, lofi_profile):
        results = diverse_recommend_songs(lofi_profile, songs, k=5, genre_penalty=3.0)
        genres = [s["genre"] for s, _, _, _ in results]
        unique_genres = set(genres)
        assert len(unique_genres) >= 2, (
            f"With genre_penalty=3.0, expected at least 2 different genres, got: {genres}"
        )


# ---------------------------------------------------------------------------
# Edge cases — adversarial inputs
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_ghost_genre_returns_k_results(self, songs):
        ghost_profile = {
            "genre": "metal", "mood": "angry",
            "energy": 0.95, "tempo": 160,
            "valence": 0.30, "danceability": 0.60,
            "likes_acoustic": False,
        }
        results = recommend_songs(ghost_profile, songs, k=5)
        assert len(results) == 5

    def test_empty_genre_and_mood(self, songs):
        profile = {
            "genre": "", "mood": "",
            "energy": 0.55, "tempo": 100,
            "valence": 0.65, "danceability": 0.65,
            "likes_acoustic": False,
        }
        results = recommend_songs(profile, songs, k=3)
        assert len(results) == 3

    def test_extreme_low_values(self, songs):
        profile = {
            "genre": "ambient", "mood": "chill",
            "energy": 0.0, "tempo": 0,
            "valence": 0.0, "danceability": 0.0,
            "likes_acoustic": True,
        }
        results = recommend_songs(profile, songs, k=3)
        assert len(results) == 3
        for _, score, _ in results:
            assert isinstance(score, float)

    def test_k_larger_than_catalog(self, songs):
        profile = {"genre": "pop", "mood": "happy", "energy": 0.7}
        results = recommend_songs(profile, songs, k=99999)
        assert len(results) == len(songs)

    def test_k_zero_returns_empty(self, songs):
        profile = {"genre": "pop", "mood": "happy", "energy": 0.7}
        results = recommend_songs(profile, songs, k=0)
        assert results == []


# ---------------------------------------------------------------------------
# Frequency profile mapper — unit tests
# ---------------------------------------------------------------------------

class TestFrequencyMapper:
    def test_high_sub_bass_disables_acoustic(self):
        freq = {"sub_bass": 0.9, "bass_warmth": 0.5,
                "vocal_presence": 0.5, "brightness": 0.5, "groove_weight": 0.5}
        prefs = freq_to_audio_prefs(freq, {"energy": 0.5})
        assert prefs["likes_acoustic"] is False

    def test_high_sub_bass_boosts_energy(self):
        freq = {"sub_bass": 0.9, "bass_warmth": 0.5,
                "vocal_presence": 0.5, "brightness": 0.5, "groove_weight": 0.5}
        prefs = freq_to_audio_prefs(freq, {"energy": 0.3})
        assert prefs["energy"] > 0.3

    def test_high_vocal_presence_lowers_instrumentalness(self):
        freq = {"sub_bass": 0.5, "bass_warmth": 0.5,
                "vocal_presence": 0.9, "brightness": 0.5, "groove_weight": 0.5}
        prefs = freq_to_audio_prefs(freq, {"instrumentalness": 0.8})
        assert prefs["instrumentalness"] < 0.8

    def test_low_brightness_caps_valence(self):
        freq = {"sub_bass": 0.5, "bass_warmth": 0.5,
                "vocal_presence": 0.5, "brightness": 0.2, "groove_weight": 0.5}
        prefs = freq_to_audio_prefs(freq, {"valence": 0.99})
        assert prefs["valence"] <= 0.72

    def test_freq_to_weights_returns_all_keys(self):
        freq = {"sub_bass": 0.7, "bass_warmth": 0.7,
                "vocal_presence": 0.6, "brightness": 0.3, "groove_weight": 0.8}
        weights = freq_to_weights(freq)
        from src.recommender import STRATEGIES
        for key in STRATEGIES["balanced"]:
            assert key in weights, f"Missing weight key: {key}"

    def test_freq_to_weights_amplifies_danceability_for_groove(self):
        freq_groove = {"sub_bass": 0.5, "bass_warmth": 0.5,
                       "vocal_presence": 0.5, "brightness": 0.5, "groove_weight": 0.9}
        freq_flat   = {"sub_bass": 0.5, "bass_warmth": 0.5,
                       "vocal_presence": 0.5, "brightness": 0.5, "groove_weight": 0.1}
        w_groove = freq_to_weights(freq_groove)
        w_flat   = freq_to_weights(freq_flat)
        assert w_groove["danceability"] > w_flat["danceability"]

    def test_freq_mapper_does_not_mutate_base_prefs(self):
        freq = {"sub_bass": 0.9, "bass_warmth": 0.5,
                "vocal_presence": 0.5, "brightness": 0.5, "groove_weight": 0.5}
        original = {"energy": 0.3, "likes_acoustic": True}
        import copy
        before = copy.deepcopy(original)
        freq_to_audio_prefs(freq, original)
        assert original == before, "freq_to_audio_prefs mutated the base_prefs dict"
