# Model Card: Cultural Frequency Music Recommender

## 1. Model Name

**Cultural Frequency Intelligence v2.0**
*(Built on VibeScore 1.0 — Music Recommender Simulation, Modules 1–3)*

---

## 2. Intended Use

This system takes a natural language music request — *"I want that deep bass Sunday morning soul feel"* — and returns a ranked list of songs with a culturally-grounded explanation of why they match. It uses Claude (claude-opus-4-7) to parse intent, a RAG pipeline backed by a hand-curated Black American music heritage knowledge base, a frequency profile system that maps cultural descriptors to sonic dimensions, and a weighted scoring engine to rank songs across 10+ audio features.

The system is built for educational purposes and portfolio demonstration. It is not connected to a licensed music catalog — the song data is fictional sample data. Its purpose is to demonstrate how a full AI pipeline can honor cultural knowledge rather than flatten it.

---

## 3. How the Model Works

**Step 1 — Intent Parsing (Claude API):** The user's natural language input is sent to Claude with a structured system prompt. Claude returns a JSON object containing audio preferences (genre, mood, energy, tempo, valence, danceability), a five-dimension frequency profile (sub_bass, bass_warmth, vocal_presence, brightness, groove_weight), a list of cultural query terms, and a reasoning trace.

**Step 2 — RAG Retrieval:** The cultural query terms and dominant frequency dimension are used to search `cultural_kb.json` across three passes: direct catalog tag match, dominant frequency dimension match, and keyword match. The retriever returns matched genre entries with their cultural lineage, sonic descriptions, and frequency signatures.

**Step 3 — Frequency Mapping:** The frequency profile is mapped to audio preference overrides (e.g. high sub_bass → low acousticness, high danceability) and custom scoring weights (e.g. high groove_weight → amplify danceability and tempo weights).

**Step 4 — Scoring Engine:** Every song in the catalog is scored against the merged preferences. Categorical matches (genre, mood) earn fixed points. Continuous features (energy, tempo, valence, danceability, liveness, instrumentalness) earn partial credit based on proximity to the target. Songs are sorted by total score and the top K are returned.

**Step 5 — Cultural Explanation (Claude API, streaming):** The top K songs, retrieved cultural context, and original user input are passed to Claude, which streams a 3-5 sentence explanation connecting the recommendations to Black American music history and the specific frequency characteristics the listener is reaching for.

The system also supports four ranking strategies (balanced, genre-first, mood-first, energy-focused), a greedy diversity penalty that reduces scores for repeated artists and genres, a structured logger, and a heuristic fallback that activates if the Claude API is unavailable.

---

## 4. Data

**Song catalog:** `songs.csv` contains fictional sample songs across 14 genres (pop, lofi, rock, jazz, ambient, synthwave, indie pop, classical, folk, hip hop, electronic, reggae, world, country). Each song has 15 audio features including energy, tempo, valence, danceability, acousticness, liveness, instrumentalness, popularity, release decade, genre, mood, and mood tag. The catalog was generated as sample data — the artists and titles are not real.

**Cultural knowledge base:** `cultural_kb.json` was hand-curated and contains 10 genre entries covering hip-hop, jazz, gospel, soul, funk, R&B, neo-soul, blues, reggae, and lo-fi. Each entry includes cultural origins, frequency signatures, audio feature hints, sonic descriptions, and keywords. A frequency vocabulary section maps cultural terms (soulful, groovy, warm, chest-thumping) to frequency dimension values.

---

## 5. Strengths

The system's biggest strength is the frequency profile system. By translating cultural descriptors into five sonic dimensions — sub_bass, bass_warmth, vocal_presence, brightness, groove_weight — it can surface relevant songs from genres that don't share a label with the user's request. A "Sunday morning soul feel" query returned reggae, jazz, country, lofi, and world music — five different genres that all share the same warm, mid-tempo sonic pocket.

The RAG architecture keeps Claude's cultural explanations grounded. Instead of generating cultural context from training data (which can hallucinate), the system retrieves specific lineage information from the knowledge base and passes it as context. The explanations are consistently accurate to the cultural roots they reference.

The reliability layer also works well. The heuristic fallback activates automatically on API failure, the guardrails log every failure mode, and the 31-test harness catches regressions before they surface in production.

---

## 6. Limitations and Bias

**Catalog bias:** The song catalog is fictional and contains only one or two songs per genre. This means genre label matches are near-guaranteed top results regardless of how well the song fits the user's numeric preferences. A real catalog of hundreds of songs would allow the numeric scoring to do more meaningful work.

**Genre label dominance:** Categorical matches (genre, mood) award fixed points that can outweigh continuous feature mismatches. The "High Energy + Chill Mood" adversarial profile exposed this — slow lofi songs were recommended to a user with energy target 0.95 because the genre and mood labels overrode the energy penalty.

**Hand-designed frequency dimensions:** The five frequency dimensions were designed based on cultural research and personal knowledge of Black American music, not derived from data. They capture what matters about the sonic identity of these genres, but they remain a simplification. Some musical vibes don't map cleanly onto these five dimensions.

**No real song data:** Because the catalog is fictional, recommendations cannot map to actual artists a user could go listen to. This limits the system's real-world utility and means the cultural explanations Claude generates cannot be validated against actual tracks.

---

## 7. Evaluation

**Automated testing:** 31 tests across 6 classes in `tests/test_harness.py` — all passing. Tests cover: consistency (same profile → same top-3 across runs), precision (top result genre matches profile), strategy coverage (all 4 strategies return valid results), diversity (penalty correctly spreads genres), edge cases (ghost genres, extreme values, empty labels, k > catalog), and frequency mapper unit tests.

**Adversarial profiles tested:**
- Ghost Genre (metal/angry — neither exists in catalog): system fell back to pure numeric scoring, returned rock as closest match
- High Energy + Chill Mood (contradictory profile): categorical labels won over numeric targets — lofi songs recommended for energy 0.95 request
- Acoustic Headbanger (acoustic preference + rock/intense): genre and mood match won, acoustic preference silently ignored
- No Genre No Mood (numeric only): pure numeric scoring worked correctly, surfaced diverse cross-genre results
- Extreme Low (all values 0): system returned valid results without crashing, scores were appropriately low

**What surprised me during testing:** The `BadRequestError` from the Anthropic API was indistinguishable between a malformed request and an empty credit balance. Both triggered the same fallback path. The system appeared functional even when Claude was completely inaccessible — which could give a false sense of reliability. A well-designed system should surface *why* it fell back, not just that it did.

---

## 8. AI Collaboration

This system was built in close collaboration with Claude Code (claude-sonnet-4-6). The AI wrote the majority of the code across `claude_agent.py`, `cultural_retriever.py`, `frequency_profile.py`, `logger.py`, and the test harness, based on architectural decisions worked through in conversation.

**Where AI was most helpful:** Translating personal cultural knowledge into a structured data model. When I described my connection to certain bass frequencies and what "Sunday morning soul feel" meant to me culturally, Claude translated that into five concrete frequency dimensions with specific numeric ranges and a mapping from cultural keywords to audio feature values. That bridge — from personal cultural knowledge to a structured scoring system — became the most distinctive part of the whole project.

**Where AI's suggestion was flawed:** The `explain_recommendations()` function originally used `thinking: {type: "adaptive"}` with streaming. This caused a `BadRequestError` in certain configurations because adaptive thinking and streaming have constraints on `claude-opus-4-7` that weren't surfaced until actual testing. The code was written confidently without flagging this as a potential issue. This reinforced that AI-generated code must be run and tested — not just read and trusted.

---

## 9. Future Work

- Replace `songs.csv` with real Spotify API data so recommendations map to actual artists and tracks
- Expand `cultural_kb.json` with sub-genres: trap, afrobeats, neo-soul, Chicago blues, New Orleans jazz
- Add a minimum numeric fit threshold before categorical bonuses fire — prevents label dominance over strong numeric mismatches
- Cache parsed intent across a session so repeated similar queries reuse the frequency profile
- Add a confidence signal to the output — the current score (e.g. 11.22/12.5) already functions as one, but surfacing it as an explicit "how confident is this match" metric would improve transparency

---

## 10. Reflection

Building this project changed how I think about AI systems. The hardest part wasn't the code — it was deciding what the system should *know* and *care about*. Writing `cultural_kb.json` by hand forced me to think carefully about Black American music history: why the 808 bass carries the weight it does, where the gospel-to-soul-to-hip-hop lineage shows up in the actual frequency spectrum. That knowledge doesn't come from a model's training data — it comes from people. The RAG architecture made me realize that the most important part of a good AI system is often the knowledge you curate *before* the model ever sees a query.

I also learned that reliability is a design choice, not an afterthought. The heuristic fallback, input guardrails, structured logger, and test harness weren't extras added at the end — they were what made the system trustworthy enough to actually use. A recommendation that comes back with a confident cultural explanation built on hallucinated context is worse than no recommendation at all. Every layer of this pipeline exists to make sure the output earns its confidence.
