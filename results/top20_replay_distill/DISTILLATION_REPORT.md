# Kaggriculture top-20 public replay distillation — 2026-09-30

## Data and provenance

- Froze the Kaggle CLI leaderboard at 2026-09-30 00:50 UTC: 20 teams, ranks 1–20, in `targets.csv`.
- Listed public episodes for each selected team submission. Selected six recent completed episodes per team (120 selections, 96 unique matches).
- Downloaded and hash-recorded all 96 public replays. Parsed 166 top-20 player trajectories and 119,354 aligned observation/action pairs, accounting for the replay action offset (`steps[s+1].action` belongs to `steps[s].observation`).
- Raw replays and action tapes remain local research data. The submitted archive contains no replay, action tape, rival source code, or opponent private observation.

## What the replay evidence showed

- The top two agents averaged 190–203 `PASS` worker commands and 497–498 `COLLECT_FERTILIZER` commands per episode. The existing V4 agent averaged 500.5 and 389.6 respectively over eight fresh self-play seeds, both seats.
- In public top-two replay states with a cow that was fed and cared for, yielded no product, and had fertilizer available, `COLLECT_FERTILIZER` was chosen 1,403 times out of 1,558 worker decisions; `PASS` was chosen once.
- The adopted rule changes one idle worker's `PASS` to `COLLECT_FERTILIZER` only when that worker is alone on a cow tile and fertilizer is already available. The existing route and all market decisions remain computed by V4.

## Rejected alternatives

- Fixed replay tapes and state-conditioned full-action nearest-neighbor imitation failed independent official-engine games against V4.
- Copying top-two market openings or short market prefixes lost all local paired tests against V4. One-turn cattle and wheat purchases were particularly costly because they disrupted the parent market plan.
- Moving idle workers out of locked tiles also lost all local paired tests.
- A broad all-animal fertilizer residual won more games than it lost in one official batch, but the cow-only rule was more consistent in local search and the first official batch.

## Final candidate validation

- Local simulator: `kg373_gold_20260922/fast_sim` with recorded 1.32.7 parity gate (1,000/1,000 fixed-stream parity tests). Search-only cow-residual screen on 32 seeds, both seats: 45 wins, 15 losses, 4 draws; mean bank delta +15.75. This was used only to choose a candidate.
- Official `kaggle_environments` 1.32.7 engine on **fresh** 64 seeds, both seats, against V4: 128 games, 85 wins, 37 losses, 6 draws, zero agent errors. Half-win rate 68.75%; median terminal bank delta +2, mean delta −13.4375. Seats share the same seed and are not independent observations. This is a small, win-rate-oriented change; the bankroll effect is approximately neutral relative to ~100,000-bank games.
- The submission `main.py` is byte-identical to the official-engine-tested `candidate_fert_cow/main.py`; see `submission_top20_distilled_20260930/PAYLOAD_AUDIT.json` for SHA-256 and the exact archive contents.

## Interpretation

The public replays support a narrow, robust correction to a strong existing route policy. They do not establish that the agent will reach the current top-20 leaderboard ratings; those ratings depend on hosted opponent matches. The actual Kaggle score should be read from the hosted submission after evaluation.

## Submission

Kaggle CLI submission was performed once for this request. Hosted ID `56693932` completed package processing; its initial public score was 600.0 at readback. This is the starting rating and may change as hosted matches are played. The exact uploaded archive SHA-256 was `5ce306d56ef87bfc705ea27ffc760c95ad84577dd47620792e0b51803da369d0`.

## Correction after hosted replay review — 2026-09-30

The direct-call official-engine diagnostics above did **not** exercise Kaggle's path-based file loader. Hosted validation episode `115524635` ran both copies of submission `56693932` as all-PASS agents, each finishing with exactly 3,000 coins. Public match replays `115526601`, `115529883` and `115536726` show the same 3,000-coin behavior. The submission was accepted as `COMPLETE` but did not execute the intended policy.

The installed Kaggle 1.32.7 loader selects the **last callable value inserted into the module namespace**, not necessarily the function currently named `agent`. Our wrapper reassigned an existing `agent` key after defining a new `_top20_fert_repair` helper. Reassignment preserved the old insertion order, so the loader selected `_top20_fert_repair`, passing it the observation and configuration. It returned the configuration as an action; the engine normalized this to `PASS`. This was a packaging/entrypoint defect, not an evaluated strategic loss.

The local file `candidate_fert_cow_fixed/main.py` appends `submission_agent = agent` as the last inserted callable. A path-based 1.32.7 engine run then produced a nonempty first market action and 193,914 terminal coins against `random` in the tested seed. The submitted archive remains unchanged and broken. No second submission has been made for this correction.
