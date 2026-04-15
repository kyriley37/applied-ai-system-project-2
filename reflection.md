# Reflection: Profile Comparisons

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
