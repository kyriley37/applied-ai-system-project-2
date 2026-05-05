# Cultural Frequency Music Recommender


**Video Walkthrough:** [Watch on Loom](https://www.loom.com/share/f8efa7230c7a448c99b13834aa7d1a11)

---

## Original Project

This project builds on the **Music Recommender Simulation** from Modules 1–3. The original system represented songs and listener profiles as structured data, scored a 17-track catalog against user preferences using a hand-designed weighted algorithm, and returned the top K matches with plain-language explanations. Its goal was to explore how real-world recommenders turn structured data into ranked predictions — and where bias and unfairness can emerge in systems like these.

---

## What This Project Does — and Why It Matters

The Cultural Frequency Music Recommender upgrades the original system into a full AI pipeline grounded in **Black American music heritage and sonic frequency science**. Instead of filling out a form, you describe what you want to hear in plain language — *"I want that deep bass Sunday morning soul feel"* — and the system translates that cultural and emotional description into a structured frequency profile, retrieves relevant cultural context from a curated knowledge base, scores your song catalog against your actual sonic preferences, and streams a culturally-grounded explanation of why the recommendations resonate.

This matters because music taste isn't just genre checkboxes. It's frequency, lineage, and feeling. The 808 sub-bass in hip-hop and the bass guitar in gospel carry the same chest-thumping low-end energy because they share a cultural root. This system tries to honor that connection rather than flatten it.

---

## Architecture Overview

```
User Natural Language
        │
        ▼
┌─────────────────────┐
│  Claude Intent Parser│  ← Translates words into a structured
│  (claude-opus-4-7)  │    frequency profile + cultural query
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  RAG Retriever      │  ← Searches cultural_kb.json for matching
│  cultural_kb.json   │    genre lineage, sonic DNA, and cultural roots
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Frequency Mapper   │  ← Maps sub_bass/warmth/groove/vocal_presence
│  + Scoring Engine   │    to audio feature weights, then scores every
│  songs.csv          │    song in the catalog
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Claude Explainer   │  ← Streams a cultural explanation connecting
│  (Adaptive Thinking)│    the results to Black music history
└─────────┬───────────┘
          │
          ▼
    Ranked Results
    + Cultural Explanation
```

**System diagram** (full Mermaid flowchart): [assets/system_diagram.mmd](assets/system_diagram.mmd) — paste into [mermaid.live](https://mermaid.live) to render.

The pipeline has three reliability layers built in: a structured logger that records every API call and scoring decision, input guardrails with a heuristic fallback if Claude is unavailable, and a 31-test harness that validates consistency, precision, strategy coverage, diversity penalties, and edge cases.

---

## Setup Instructions

### 1. Clone and install dependencies

```bash
git clone <your-repo-url>
cd applied-ai-system-project-2
python -m venv .venv
source .venv/bin/activate      # Mac/Linux
# .venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 2. Add your Anthropic API key

```bash
cp .env.example .env
```

Open `.env` and replace the placeholder:

```
ANTHROPIC_API_KEY=sk-ant-...your key here...
```

Get a key at [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys). You'll need a small credit balance ($5–10 is plenty for experimentation).

### 3. Run the app

**Interactive mode** (requires API key):
```bash
python -m src.main
```

**Demo mode** (no API key required — runs pre-built profiles):
```bash
python -m src.main --demo
```

### 4. Run the tests

```bash
pytest tests/ -v
```

---

## Sample Interactions

### Example 1 — Sunday morning soul feel

**Input:**
```
What are you feeling? > I want that deep bass Sunday morning soul feel
```

**Output (ranked table):**
```
╭────┬──────────────────────┬──────────────┬──────────┬─────────╮
│    │ Title / Artist       │ Genre / Mood │  Energy  │  Score  │
├────┼──────────────────────┼──────────────┼──────────┼─────────┤
│ #1 │ Sunrise City         │ pop          │   0.82   │  13.5   │
│    │ Neon Echo            │ happy        │          │         │
│ #2 │ Rooftop Lights       │ indie pop    │   0.76   │  11.91  │
│    │ Indigo Parade        │ happy        │          │         │
│ #3 │ City Pulse           │ hip hop      │   0.85   │   9.43  │
│    │ Beat District        │ energetic    │          │         │
╰────┴──────────────────────┴──────────────┴──────────┴─────────╯
```

**Claude's cultural explanation (streamed):**
> That happy mood you're chasing? It lives in the **bright upper-mids (2-5kHz)** — the same frequency zone where gospel choirs lift the roof on Sunday morning, where Stevie's harmonica cuts through on "Isn't She Lovely," where joy literally vibrates. "Sunrise City" and "Rooftop Lights" sit right in that uplifting pocket, light on sub-bass but rich in that shimmering presence range that traces all the way back to tambourines in storefront churches and handclaps on Motown sessions. "City Pulse" brings the hip-hop lineage in — that energetic boom bap pulse is the great-grandchild of funk's one-drop, the same groove DNA James Brown bottled in the '60s. Your spirit knows what it needs: that bright, communal, *we-made-it-through* frequency that Black music has been broadcasting on for a hundred years — and today, you're tuned right in.

---

### Example 2 — Demo mode: Chill Lofi profile

**Command:** `python -m src.main --demo`

**Profile:** `genre=lofi, mood=chill, energy=0.38, tempo=78`

**Standard vs. Diversity penalty comparison:**
```
Standard (no penalty):
╭────┬───────────────────┬───────┬───────╮
│ #1 │ Library Rain      │ lofi  │  9.20 │
│ #2 │ Midnight Coding   │ lofi  │  8.91 │
│ #3 │ Foggy Commons     │ lofi  │  8.45 │

Diverse (artist -2.0 | genre -1.0):
╭────┬───────────────────┬────────────┬───────┬───────┬─────────╮
│ #1 │ Library Rain      │ lofi       │  9.20 │  9.20 │   —     │
│ #2 │ Midnight Coding   │ lofi       │  8.91 │  7.91 │  -1.0   │
│ #3 │ Rainy Tokyo       │ ambient    │  7.80 │  7.80 │   —     │
│ #4 │ Late Night Jazz   │ jazz       │  7.50 │  7.50 │   —     │
```

The diversity penalty surfaces music from adjacent genres (ambient, jazz) instead of returning three lofi tracks in a row.

---

### Example 3 — Demo mode: Strategy comparison

The same Chill Lofi profile ranked across all four strategies:

```
--- Strategy: BALANCED ---
  #1  Library Rain (lofi, chill)  score=9.20
  #2  Midnight Coding (lofi, chill)  score=8.91

--- Strategy: GENRE-FIRST ---
  #1  Library Rain (lofi, chill)  score=12.40   ← genre weight 4x higher
  #2  Midnight Coding (lofi, chill)  score=11.80

--- Strategy: MOOD-FIRST ---
  #1  Library Rain (lofi, chill)  score=11.10   ← mood/mood_tag weights dominate
  #2  Foggy Commons (lofi, chill)  score=10.50

--- Strategy: ENERGY-FOCUSED ---
  #1  Paper Drift (ambient, chill)  score=8.30   ← low-energy songs from any genre
  #2  Library Rain (lofi, chill)  score=8.10
```

Energy-focused is the only strategy that breaks out of the lofi bubble — it ranks by sonic feel, not genre label.

---

## Design Decisions

### Why frequency dimensions instead of just genre/mood tags?

Genre labels collapse a lot of nuance. "Hip-hop" and "gospel" look nothing alike on paper, but both can carry that same chest-thumping sub-bass weight. The five frequency dimensions — `sub_bass`, `bass_warmth`, `vocal_presence`, `brightness`, `groove_weight` — describe *how music feels in your body*, not just what shelf it belongs on. This lets the system connect cultural descriptors like "warm", "groovy", or "Sunday morning" to actual audio features without requiring the user to know music theory.

### Why Claude for intent parsing instead of a simple keyword matcher?

A keyword matcher would catch "jazz" but miss "warm late-night feel" or "something like a slow Sunday." Claude maps the full cultural and emotional weight of a sentence onto structured numeric values. The heuristic fallback (keyword-based) is still there as a safety net if the API is unavailable, but it's intentionally limited.

### Why RAG for cultural context?

The knowledge base (`cultural_kb.json`) stores hand-curated information about Black American music genres — origins, cultural roots, frequency signatures, sonic DNA. Instead of asking Claude to recall this from training data (which can hallucinate or flatten nuance), the system retrieves the relevant entries and passes them to the explainer as grounded context. This keeps the explanations accurate and rooted in real cultural lineage.

### Trade-offs

| Decision | Benefit | Cost |
|---|---|---|
| Claude for intent parsing | Rich natural language understanding | API cost + latency per query |
| Adaptive thinking on explainer | Deeper, more nuanced cultural connections | Slightly slower streaming |
| Prompt caching on system prompts | Reduced API cost on repeated queries | Adds complexity to message format |
| Heuristic fallback | App stays functional without API | Fallback profiles are shallow |
| Fictional song catalog | No licensing issues, easy to test | Results don't map to real artists |

---

## Testing Summary

**31 tests across 6 test classes** — all passing (`pytest tests/ -v`):

| Class | What it checks |
|---|---|
| `TestConsistency` | Same profile → identical top-3 across multiple runs |
| `TestPrecision` | Top result genre matches the profile's dominant genre; scores are descending |
| `TestStrategyCoverage` | All 4 strategies return k valid results with non-negative scores |
| `TestDiversity` | `diverse_recommend_songs` applies penalties correctly and spreads genres |
| `TestEdgeCases` | Ghost genres, empty labels, extreme zeros, k > catalog size, k=0 |
| `TestFrequencyMapper` | `freq_to_audio_prefs` and `freq_to_weights` behave correctly; no mutation of inputs |

**What worked well:**
- The scoring engine is fully deterministic — consistency tests passed on the first run
- Frequency mapper correctly amplifies the right weights (high groove → higher danceability weight)
- Diversity penalty reliably surfaces songs from different genres when the penalty is strong enough

**What was harder than expected:**
- `claude-opus-4-7` with structured outputs rejects certain parameter combinations silently as `BadRequestError` — wrapping the parse call in a try/except with a heuristic fallback was essential
- The `BadRequestError` also fires on insufficient API credits, which looks identical to a malformed request — the error handling catches both correctly but the user experience is the same either way

**What I'd improve with more time:**
- Replace `songs.csv` with real Spotify API data so recommendations map to actual artists
- Add more entries to `cultural_kb.json` for sub-genres (neo-soul, trap, afrobeats)
- Cache the parsed intent across a session so repeated queries with similar phrasing reuse the profile

---

## Reflection

Building this project changed how I think about AI systems. The hardest part wasn't the code — it was deciding what the system should *know* and *care about*. Writing `cultural_kb.json` by hand forced me to think carefully about Black American music history: why the 808 bass carries the weight it does, where the gospel-to-soul-to-hip-hop lineage shows up in the actual frequency spectrum. That knowledge doesn't come from a model's training data — it comes from people. The RAG architecture made me realize that the most important part of a good AI system is often the knowledge you curate *before* the model ever sees a query.

I also learned that reliability is a design choice, not an afterthought. The heuristic fallback, input guardrails, structured logger, and test harness weren't extras I added at the end — they were what made the system trustworthy enough to actually use. A recommendation that comes back with a confident cultural explanation built on a hallucinated context is worse than no recommendation at all. Every layer of this pipeline exists to make sure the output earns its confidence.

---

## Project Structure

```
applied-ai-system-project-2/
├── src/
│   ├── main.py               # Entry point — interactive + demo modes
│   ├── recommender.py        # Scoring engine, ranking strategies, diversity penalty
│   ├── claude_agent.py       # Claude API: intent parser + streaming explainer
│   ├── cultural_retriever.py # RAG: 3-pass retrieval from cultural_kb.json
│   ├── frequency_profile.py  # Frequency → audio prefs + scoring weight mapper
│   └── logger.py             # Structured JSON logging
├── data/
│   ├── songs.csv             # Song catalog (fictional sample data)
│   └── cultural_kb.json      # Black American music heritage knowledge base
├── tests/
│   ├── test_recommender.py   # Original unit tests
│   └── test_harness.py       # Reliability + consistency harness (31 tests)
├── assets/
│   └── system_diagram.mmd    # Mermaid architecture diagram
├── model_card.md
├── reflection.md
├── requirements.txt
└── .env.example
```
