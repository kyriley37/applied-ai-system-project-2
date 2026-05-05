# Reflection

---

## Responsible AI: Limitations, Bias, and Collaboration

### What are the limitations or biases in your system?

The most significant bias is **catalog bias** — the song catalog (`songs.csv`) is fictional and was generated as sample data. Every recommendation the system makes is constrained by what's in that catalog, and a fictional catalog doesn't reflect the actual diversity of music that exists. If real data were used, bias could creep in through underrepresentation — for example, if the catalog contained fewer jazz or gospel songs relative to pop, those genres would be systematically disadvantaged no matter how well the scoring engine worked.

The second limitation is **genre label dominance**. Genre and mood are categorical matches — they either fire or they don't. A genre match is worth more points than a near-perfect energy or tempo match in most strategies. This means a mediocre song in the right genre will beat a great song in the wrong genre, which doesn't reflect how people actually experience music.

The third limitation is the **frequency profile itself**. The five dimensions (sub_bass, bass_warmth, vocal_presence, brightness, groove_weight) were hand-designed based on cultural research, not derived from data. They capture what I believe matters about Black American music's sonic identity, but they're still a simplification. Someone could describe a vibe that doesn't map cleanly onto these five dimensions, and the system would still return a result without signaling that the mapping was uncertain.

---

### Could your AI be misused, and how would you prevent that?

The most realistic misuse is **cultural flattening** — using the cultural knowledge base to generate explanations that sound authoritative about Black music history without actually being correct or respectful. Claude can produce confident-sounding cultural context that is partially inaccurate, and a user might not know the difference.

The knowledge base (`cultural_kb.json`) is the main defense against this: by providing grounded, hand-curated context rather than letting Claude improvise from training data, the explanations stay anchored to real cultural facts. The other prevention is transparency — the system shows its scoring reasons alongside every recommendation, so users can see *why* a song was chosen rather than just accepting the explanation at face value.

A less obvious misuse: the system could theoretically be used to generate playlists that exploit cultural associations for commercial purposes without acknowledgment of their origins — "Sunday morning soul feel" as a marketing aesthetic stripped of its cultural meaning. That's harder to prevent technically, but naming it explicitly is a start.

---

### What surprised you while testing the AI's reliability?

The most surprising thing was how the `BadRequestError` from the Anthropic API was indistinguishable between two completely different failure modes — a malformed request and an empty credit balance. Both returned the same error type and triggered the same fallback. This meant the system appeared to "work" (it returned songs via the heuristic fallback) even when the API was completely inaccessible, which could give a false sense of reliability. A well-designed system should surface *why* it fell back, not just that it did.

The second surprise was how robust the scoring engine was to adversarial inputs. The ghost genre profile (metal/angry — neither exists in the catalog) still returned five reasonable songs using only numeric scoring. The extreme-zeros profile still returned valid results. The system didn't crash or return empty lists — it just quietly did the best it could with what it had. That's a good kind of surprise.

---

### Collaboration with AI during this project

This project was built in close collaboration with Claude Code (claude-sonnet-4-6). The AI wrote most of the code across `claude_agent.py`, `cultural_retriever.py`, `frequency_profile.py`, `logger.py`, and the test harness, based on architectural decisions we worked through together in conversation.

**One instance where the AI was genuinely helpful:** When designing the frequency profile system, I described my personal connection to certain bass frequencies and what "Sunday morning soul feel" meant to me culturally. Claude translated that into five concrete dimensions with specific numeric ranges and a mapping from cultural keywords to frequency values. That bridge — from personal cultural knowledge to a structured data model — is something I couldn't have designed as quickly on my own, and it became the most distinctive part of the whole system.

**One instance where the AI's suggestion was flawed:** The `explain_recommendations()` function in `claude_agent.py` originally used `thinking: {type: "adaptive"}` with streaming. This caused a `BadRequestError` in certain configurations because adaptive thinking and streaming have constraints on `claude-opus-4-7` that weren't immediately obvious. The AI wrote the code confidently without flagging this as a potential issue, and it only surfaced during actual testing. The fix was straightforward once the error appeared, but it reinforced that AI-generated code needs to be run and tested — not just read and trusted.

---

# Profile Comparisons

## High-Energy Pop vs. Chill Lofi

These two profiles are basically opposites. The pop profile wants fast, upbeat songs with high energy, and it got Sunrise City at the top — which is pop, happy, and energetic. The lofi profile wants slow, quiet, acoustic songs, and it got Midnight Coding and Library Rain — which are both lofi and chill. The rankings made sense for both. What is interesting is how cleanly the energy score separated them. Sunrise City (energy 0.82) scored near the top for pop and near the bottom for lofi, while Library Rain (energy 0.35) did the opposite. The system understood the difference between these two listener types clearly.

---

## Deep Intense Rock vs. Late Night Jazz

Both of these profiles wanted a very specific genre and only one song in the catalog matched each. Storm Runner was the only rock song and scored 7.26 for the rock profile. Coffee Shop Stories was the only jazz song and scored 7.25 for the jazz profile. The #1 results were obvious and correct. But the drop to #2 was dramatic for both — the rock profile went from 7.26 down to 3.74, and jazz went from 7.25 down to 3.81. That gap tells you the system is not really ranking well for these users — it is just finding one great match and then guessing on the rest. A jazz fan who cannot find more jazz should ideally get acoustic or relaxed songs next, which it did get (Moonlit Cabin, Island Breeze), but it felt more like luck than logic.

---

## Ghost Genre (metal/angry) vs. No Genre No Mood

The ghost genre profile had a genre and mood that do not exist in the catalog, so those bonuses never fired. The no genre no mood profile deliberately left those fields blank. Both profiles ended up relying purely on numeric scoring. The ghost genre profile got Storm Runner at the top because it was closest in energy and tempo to metal. The no genre no mood profile got Crystal Lagoon at the top — a completely different song — because it matched best on energy, tempo, valence, and danceability around the middle range. The interesting difference is that the ghost genre profile was chasing extreme high-energy songs (0.95), while the no genre no mood profile was targeting the middle (0.55), so they surfaced totally different parts of the catalog even though both were doing pure numeric matching. This shows the numeric scoring does actually work on its own — it just needs realistic targets.

---

## High Energy + Chill Mood vs. Acoustic Headbanger

Both of these profiles had internal contradictions built in on purpose. The high energy + chill mood profile said "I want lofi and chill but also energy 0.95." The acoustic headbanger said "I want rock and intense but also acoustic." The results were very different. The acoustic headbanger got Storm Runner at #1 with a strong score of 6.47 because genre and mood matched perfectly and the acousticness preference was just quietly ignored — Storm Runner is not acoustic but the rest of its features were close enough. The high energy + chill mood profile got slow lofi songs at the top because the genre and mood match outweighed the energy mismatch. So one contradiction was silently ignored (acoustic preference in rock), and the other took over the whole ranking (mood wins over energy). The system handled the two contradictions very differently, which is not fair or predictable from a user's perspective.

---

## Chill Lofi vs. High Energy + Chill Mood (same genre and mood, different energy)

This is the most direct comparison showing the filter bubble. Both profiles said genre lofi and mood chill. The only difference was energy: 0.38 for the normal chill lofi user versus 0.95 for the contradictory one. Both got Midnight Coding and Library Rain as their top two results. The scores were lower for the contradictory profile (4.55 vs 7.25), which shows the system noticed the energy mismatch and penalized it. But it still recommended the same songs. A real music app would recognize that someone asking for energy 0.95 does not want lofi regardless of what genre they typed — but this system cannot make that judgment because genre and mood always win.
