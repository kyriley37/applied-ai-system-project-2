# Model Card: Music Recommender Simulation

## 1. Model Name

**VibeScore 1.0**

---

## 2. Intended Use

VibeScore 1.0 suggests songs from a small catalog based on a listener's stated taste preferences. The user describes what they want — a favorite genre and mood, numeric targets for energy, tempo, valence, and danceability, whether they like acoustic music, and optional fine-grained preferences like a mood tag or preferred era. The system scores every song against those preferences and returns the top matches with plain-language explanations for each result.

This system is built for classroom exploration, not real users. It assumes the user can describe their taste accurately and in advance, which real listeners rarely can. It does not learn from listening history or adapt over time. Its purpose is to show how a scoring-based recommender makes decisions and where those decisions can go wrong.

---

## 3. How the Model Works

Every song in the catalog has a set of labels and numbers attached to it — things like its genre, mood, how energetic it sounds, how fast it is, whether it feels cheerful or dark, and how acoustic or electronic it sounds. The system also knows each song's popularity score, what decade it came from, whether it feels like a live recording, and how vocal or instrumental it is.

When a user runs the recommender, they describe what they are looking for using the same kinds of labels and numbers. The system then goes through every song one by one and gives it a score based on how well it matches. A genre match is worth 1 point. A mood match is worth 1 point. A detailed mood tag match is worth 1.5 points. For numeric features like energy and tempo, the system awards partial credit — a song that is close to the target gets most of the points, and a song that is far away gets fewer or none. The closer the match across all features, the higher the total score. Songs are then sorted from highest to lowest and the top results are returned.

The system also supports four ranking strategies that shift how much each feature matters. The balanced strategy uses all features equally. The genre-first strategy makes genre the dominant signal. The mood-first strategy prioritizes emotional feel over genre. The energy-focused strategy almost ignores genre and mood and ranks entirely by rhythm and intensity. A user can switch strategies with one change.

Finally, a diversity penalty can be applied at selection time. If a song shares an artist or genre with one already in the results, its effective score is reduced — pushing the system to surface a wider variety of music.

---

## 4. Data

The catalog contains 17 songs across 14 genres including pop, lofi, rock, jazz, ambient, synthwave, indie pop, classical, folk, hip hop, electronic, reggae, world, and country. Moods represented include happy, chill, intense, relaxed, focused, moody, nostalgic, reflective, energetic, dreamy, adventurous, and romantic. Each song also carries a detailed mood tag (euphoric, focused, aggressive, melancholic, motivational, dreamy, nostalgic, uplifting, adventurous), a popularity score, a release decade, a liveness score, and an instrumentalness score.

The dataset was hand-crafted for this project. It skews toward modern music — 8 of 17 songs are tagged as 2020s, 7 as 2010s, and only 3 as 2000s or earlier. There is no music from before 2000 except for a few jazz, classical, and reggae tracks. Most genres appear only once. There is no representation of genres like R&B, metal, blues, gospel, Latin, K-pop, or country-pop. The data mostly reflects a Western, English-language taste profile and would not generalize to global listeners.

---

## 5. Strengths

The system works best when the user's taste profile closely matches one or two songs in the catalog. A "Chill Lofi" user who wants low energy, slow tempo, and acoustic sound gets highly relevant results — Midnight Coding scored 9.13 out of 12.5 with every feature firing. The explanations are also a genuine strength: every result comes with a numbered list of reasons, so a user can immediately see why a song was chosen and whether those reasons make sense to them. That kind of transparency is rare in real recommenders.

The strategy switching also works well in practice. Running the same Chill Lofi profile through all four strategies produced four different #3 results, showing that the system is genuinely sensitive to how features are weighted. The mood-first strategy in particular surfaced Spacewalk Thoughts (ambient, chill) that the balanced strategy missed — a cross-genre discovery driven purely by emotional match.

The diversity penalty is another real improvement. Without it, the top 5 for Chill Lofi included LoRoom twice and was entirely lofi. With the penalty applied, Focus Flow was displaced by Coffee Shop Stories (jazz), Spacewalk Thoughts (ambient), and Moonlit Cabin (country), giving the list genuine variety without sacrificing the top two results.

---

## 6. Limitations and Bias

The most significant weakness discovered through testing is the **single-song genre trap**: 11 out of 14 genres in the catalog appear only once, so any user whose favorite genre matches that lone song immediately receives it as a near-guaranteed #1 result regardless of how poorly the song fits their energy, tempo, or mood targets. This creates a filter bubble where users of niche genres (rock, jazz, classical, country) are locked into one recommendation with a large score gap to #2, meaning they never discover cross-genre alternatives that might actually fit them better. The weight-shift experiment made this concrete — halving the genre bonus and doubling the energy weight did not change the top result for any of the four main profiles, because a single strong genre match still outscored everything else.

A second bias appears in the "High Energy + Chill Mood" adversarial test: when a user's categorical preferences (genre, mood) conflict with their numeric ones (energy), the categorical bonuses always win. The system recommended slow lofi tracks to a user who explicitly asked for energy 0.95. Real recommenders address this by requiring a minimum threshold on numeric fit before applying categorical boosts.

The dataset itself is biased toward modern, English-language, Western music. Users whose taste centers on older decades, non-Western genres, or styles like R&B, metal, or Latin music would receive poor results not because the scoring logic is wrong but because the catalog does not represent them at all.

---

## 7. Evaluation

I tested four normal profiles and five adversarial profiles by running the recommender and reading the ranked output for each one.

**Profiles tested**

- High-Energy Pop: genre pop, mood happy, energy 0.88
- Chill Lofi: genre lofi, mood chill, energy 0.38
- Deep Intense Rock: genre rock, mood intense, energy 0.92
- Late Night Jazz: genre jazz, mood relaxed, energy 0.35
- Ghost Genre: genre metal, mood angry — neither exists in the catalog
- High Energy + Chill Mood: lofi/chill genre and mood but energy 0.95 — intentional contradiction
- Acoustic Headbanger: rock/intense with likes_acoustic True — acoustic preference conflicts with the genre
- No Genre No Mood: empty genre and mood, only numeric targets
- Extreme Low: all numeric targets set to 0

**What I was looking for**

For normal profiles I checked whether the top result matched the label and whether scores dropped off sensibly below #1. For adversarial profiles I was looking for where the system produced results that would feel wrong to a real listener.

**What surprised me**

The biggest surprise was the High Energy + Chill Mood profile. I expected the high energy target to pull in fast songs, but the system recommended slow lofi tracks instead. Midnight Coding and Library Rain both scored 4.55 even though their energy is around 0.40, far from the 0.95 target. The genre and mood bonuses together outweighed the energy penalty, so the system ignored the contradiction entirely.

The weight-shift experiment was the second surprise. Doubling the energy weight and halving the genre bonus did not change the top result for any profile. The rankings were rigid because when one song dominates on every feature, changing weights just shifts all scores up together without reordering anything.

The Ghost Genre profile showed that the numeric scoring alone is not useless — with no genre or mood match possible, the system still surfaced Storm Runner at #1 based on energy and tempo proximity. But the low ceiling (3.55 out of 12.5) showed how much the categorical bonuses carry normal profiles.

---

## 8. Future Work

The most important improvement would be expanding the catalog. With only one or two songs per genre, the system cannot make meaningful recommendations for most users. A catalog of at least 200 songs across evenly distributed genres would let the numeric features do real work instead of the genre label doing almost everything.

A minimum threshold rule would fix the categorical override problem. Before awarding a genre or mood bonus, the system could require that the song's energy is within a set range of the user's target. That way a lofi song would not earn genre points for a user who wants high-energy music, even if the genre matches.

Adding listening history would make the system more realistic. Right now every session starts fresh. A simple history that tracks which songs a user has heard before could be used to boost novelty — penalizing songs already heard and rewarding ones from genres the user has not explored yet.

The diversity penalty works but it is blunt. A more refined version could track not just artist and genre but mood tag and energy bracket, preventing the list from clustering around one emotional register even when artists and genres vary.

---

## 9. Personal Reflection

Building this showed me that a recommender system is not really about finding the "best" song — it is about defining what "best" means through weights, rules, and the data you choose to include. Every number in the scoring logic is a judgment call, and small changes to those numbers can completely change what the system prioritizes. The weight-shift experiment made that concrete: I expected doubling the energy weight to shake up the rankings, but the results barely moved because the catalog structure made genre matches so dominant.

The adversarial profiles were the most valuable part of the project. Testing a "High Energy + Chill Mood" user or a "Ghost Genre" user revealed failure modes that normal testing would never surface. Real AI systems are tested the same way — engineers deliberately try to break them to find edge cases before users do. The fact that my system confidently recommended slow, quiet lofi tracks to a user who said they wanted intense high-energy music is exactly the kind of silent failure that would go unnoticed without that kind of adversarial thinking.
