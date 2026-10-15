# Second Kaggriculture agent: an independent market-adaptive candidate

Research snapshot: 2026-09-30 08:57 UTC. The saved Kaggle leaderboard is `kaggriculture.zip` (10,195 scored teams). At that instant, rank 30 scored 2733.7, rank 509 scored 2122.2, and rank 1019 scored 1886.6. Score 2500 was around rank 118. These are moving public ratings, not final medal cutoffs.

Only the latest two submitted agents are tracked, and the **better** rating is shown for the team. They cannot be combined into an ensemble at matchmaking time. The objective for a second entry is therefore an independently competitive agent with a different failure pattern, rather than a tiny variant of `submission.tar.gz`.

## Evidence informing the design

- The first submitted agent, ID 56702533, passed hosted 720-step self-play and won its first two public games. The public score 752.9 was based on only those two games and has no settled-rating meaning. The hosted replays are in `hosted_validation/`.
- Frozen top-20 public replay tapes: ranks 1 and 2 both start every selected tape with `BUY_ANIMAL COW 1` then `BUY_PRODUCT WHEAT 5`; most other leading tapes also buy cows, sheep, and wheat early. `META_TAPE_SUMMARY.json` summarizes intended orders. Its sale quantities are **issued order quantities**, not proven fulfilled sales.
- The first agent uses a wheat buy/sell opening and many layers on a fixed public route lineage. It is sensitive to cash/order timing and competes for commonly traded wheat, fertilizer, eggs, and dairy. Its local edge over its public parent was 31–1 but usually only four coins; this does not establish strength against the current top 20.
- A previous public-replay imitation submission was accepted but played all-PASS on Kaggle because of a loader-entry error. The new ID 56702533 hosted replay confirms this particular archive actually acts, but every second archive must receive its own path-loader and hosted validation check.

## Recommended architecture

An **online market-aware portfolio planner** with a separate production route from the first agent:

1. **Independent opening candidates.** Search a small set of feasible step-0 plans (hire-first, mixed animals, crop-first, feed prebuy), including but not limited to a counter to the common cow-then-wheat opening. Score full downstream cashflow and resource feasibility; do not commit to a one-turn price attack merely because it harms a frozen replay.
2. **Adaptive production allocation.** Re-evaluate every day or when market prices/shop inventory change. Choose worker and land time among feed, animals, strawberry/tomato/melon, and fertilizer by projected *net final bank*, including labor, feed, shed capacity, and transport. Maintain at least two viable portfolio modes so the opponent's glut does not force a common-route race.
3. **Exact market-order scheduler.** Simulate order-slot timing, quote rounding, cash after each order, sales needed to fund later purchases, and competing sales inferred from public market/farm state. Optimize the probability of winning close games, not mean winning margin. Never shift buys or required feed behind unaffordable actions.
4. **Late-game cash closure.** Starting around the final three days, stop investments that cannot pay back, clear worker inventories and shed without blocking deliveries, and schedule the last sales before turn 720.

The plan may reuse correctly licensed public engine semantics and tested components, but must have independently optimized opening/production decisions and original opponent-aware market scheduling. A copied public submission with cosmetic residuals is not enough evidence of a complementary agent.

## Decision gate before spending the remaining submission

- Verify the 1.32.7 file-path loader picks the intended `agent`, and run full official-engine games, including extracted-archive games in both seats. Assert nonempty market actions and no all-PASS behavior.
- Use matched `(opponent, seed, seat)` triples with untouched holdout seeds. Include the first agent, V4, independent public strong agents that trade, and several different opening/production archetypes. Do not grade against starter, random, or a fixed action tape as if they were live rivals.
- Report win/loss and uncertainty **per opponent and per rating band**. Separate cases in which the first agent loses from cases it already wins. The second must win in at least one material difficult cluster while retaining enough lower-band wins to climb the hosted ladder.
- A single attractive average coin margin is not a pass: competition rating depends on the match result. When actual hosted episodes accumulate, use their loss patterns and seeds to calibrate the local opponent league.

No second submission is authorized by this design document and none was performed during this research.
