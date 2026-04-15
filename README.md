# Music Recommender Simulation

## Project Summary

This project builds a small music recommender system in Python. It represents songs and a user taste profile as data, scores every song in a 17-track catalog against that profile using a hand-designed algorithm, and returns the top K matches with plain-language explanations. The goal is to explore how real-world recommenders turn structured data into ranked predictions — and where bias and unfairness can sneak in.

---

## How The System Works

Each `Song` is described by its genre, mood, and five numerical traits: energy, tempo, valence, danceability, and acousticness. The `UserProfile` stores the listener's favorite genre and mood, plus numeric targets for energy, tempo, valence, and danceability, and a boolean for acoustic preference. The recommender scores every song against those preferences and returns the top K matches in ranked order.

**Data flow:** Input (UserProfile) → score every song → sort descending → return top K with reasons

### Song Features

| Feature | Type | Description |
|---|---|---|
| `genre` | string | Musical style (lofi, pop, rock, jazz, …) |
| `mood` | string | Emotional feel (chill, happy, intense, …) |
| `energy` | 0–1 float | Intensity level |
| `tempo_bpm` | float | Beats per minute |
| `valence` | 0–1 float | Cheerfulness (high = positive, low = moody) |
| `danceability` | 0–1 float | Groove and rhythmic drive |
| `acousticness` | 0–1 float | How acoustic vs. electronic the track is |

### UserProfile Fields

`favorite_genre`, `favorite_mood`, `target_energy`, `target_tempo`, `target_valence`, `target_danceability`, `likes_acoustic`

### Algorithm Recipe

Each song starts at 0 and earns points by matching the user profile:

**Categorical rules**

| Rule | Points |
|---|---|
| `genre` matches `favorite_genre` | +2.0 |
| `mood` matches `favorite_mood` | +1.0 |

**Continuous similarity rules** — formula: `max(0, 1 - |song_value - target| / tolerance) × weight`

| Feature | Tolerance | Max points |
|---|---|---|
| Energy | ±0.40 | +1.5 |
| Tempo | ±40 BPM | +1.0 |
| Valence | ±0.30 | +0.75 |
| Danceability | ±0.30 | +0.75 |

**Acousticness preference**

- `likes_acoustic = True` AND `acousticness > 0.6` → +0.5
- `likes_acoustic = False` AND `acousticness < 0.3` → +0.5

**Maximum possible score: 7.5**

### Potential Biases

- **Genre dominates.** At +2.0, a genre match outweighs a perfect mood alignment (+1.0). A great song that fits the user's mood but not their genre will always rank below a mediocre same-genre track.
- **Small catalog amplifies exact matches.** With 17 songs and 14 unique genres, a genre match is almost a guarantee of a top result — the genre weight is disproportionately powerful at this scale.
- **Numeric targets assume one ideal point.** A user who enjoys both high-energy and very low-energy songs depending on context will always get mid-energy recommendations.
- **Acousticness is binary.** Songs in the middle range (0.3–0.6) are ignored by this rule even if they would be enjoyable.

---

## Getting Started

### Setup

1. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv .venv
   source .venv/bin/activate      # Mac or Linux
   .venv\Scripts\activate         # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the app:

   ```bash
   python -m src.main
   ```

### Running Tests

```bash
pytest
```

---

## Experiments You Tried

Document the experiments you ran. For example:

- What happened when you changed the weight on genre from 2.0 to 0.5
- What happened when you added tempo or valence to the score
- How did your system behave for different types of users

---

## Reflection

See the full model card: [model_card.md](model_card.md)

Write 1–2 paragraphs here about what you learned:

- How recommenders turn data into predictions
- Where bias or unfairness could show up in systems like this
