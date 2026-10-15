# Top-20 replay counter agent: local validation (2026-09-30)

## Deliverable

- Candidate archive: `submission.tar.gz` in this directory.
- Archive SHA-256: `170a7dbd489362738844efbeae04a24114f8a427437dd7788a94c070d8d2b36d`.
- Archive members: root-level `main.py`, `LICENSE`, `NOTICE`.
- `main.py` SHA-256: `f7f6a0c330c585a71c4854a34c02d922e20c68fa0006ff00ebe82d9528562220`.
- Submitted once via Kaggle CLI on 2026-09-30. Submission ID **56702533** was `PENDING` on immediate readback. A later readback showed `COMPLETE`, initial public score 752.9 after only two public games. The reference archive at `../ready_2500_final_20260930/submission.tar.gz` was left intact. See `SUBMISSION_RECEIPT.json`.

## What changed

The agent starts with the public Tetsutani V23 policy in the reference archive. It uses the top-20 public replay analysis in `../top20_replay_distill_20260930/` to repair selected worker `PASS` decisions around cow fertilizer, animal care, and dry crops. The source is **public replay actions**, not the hidden code or weights of the top-20 agents. Broader replay imitation and extra harvest/feed actions lost in local screens and were discarded.

Two opponent-sensitive defects were identified from losses:

1. In the equal-money mirror opening, the reference policy buys and sells eight wheat. A four-wheat round trip follows the same route and gains four coins against that opening in the tested seeds. For this branch, the policy otherwise stays on the reference route.
2. Against V4, a one-unit milk sale could take an early market order slot and push a much larger tomato sale behind the rival's order. In one inspected loss this reversed a +51-coin lead into a -192-coin deficit on the next step. The final correction moves a **leading sale of at most five units** behind later sales only when another sale has at least ten units. It applies from step 144, outside the mirror branch, and only when all market orders are sales. Quantities, buying, and hiring are unchanged.

## Fresh official-engine head-to-head tests

All rows below use `kaggle-environments 1.32.7`, full 720-step games, file-path agent loading, fresh seeds excluded from candidate search, and both player seats for every seed. Every game ended `DONE`; no loader fallback was seen. “Margin” is mean final reward difference per game, candidate minus opponent. These are local head-to-head results, **not a hosted Kaggle score estimate**.

| Opponent | Seed pairs | Games | Wins–losses | Mean margin |
|---|---:|---:|---:|---:|
| Existing local V4, `../submission_ready_20260930/main.py` | 32 | 64 | **58–6** | +576.28 |
| Reference submission, `../ready_2500_final_20260930/main.py` | 16 | 32 | **31–1** | +17.34 |
| Public Adaptive Shop Guard | 8 | 16 | **16–0** | +31,669.25 |
| Public Kaito V27 | 8 | 16 | **16–0** | +43,809.81 |

On the **same 32 seed pairs against V4**, the earlier conditional candidate without the small-sale correction won **52–12**, mean margin +291.66. The final correction improved this to **58–6**, mean margin +576.28. Paired seats share a seed and are correlated; these figures describe this panel, not a guaranteed win rate against arbitrary opponents.

After packaging, the archive was extracted and `main.py` was loaded as a file path for four additional full official-engine games on seed 21200011. It won in both seats against the reference submission by four coins and against V4 by 329 coins. All four ran 720 steps with 719 active turns, `DONE`, and no fallback.

## Evidence and reproduction

- Replay inventory and aligned decisions: `../top20_replay_distill_20260930/ANALYSIS.json`, `../top20_replay_distill_20260930/WORKER_CONTEXT.json`.
- Official game rows and summary: `OFFICIAL_MARKET_SMALL5_GAMES.json`, `OFFICIAL_MARKET_SMALL5_SUMMARY.json`.
- Matched earlier-candidate control: `candidate_conditional/main.py` and the `conditional_vs_v4_control` row in that summary.
- Archive member/hash audit: `PAYLOAD_AUDIT.json`.
- Extracted-archive test: `ARCHIVE_PATH_VALIDATION.json`.
- Reproduction scripts: `official_market_small5.py`, `package_final.py`, `validate_archive.py`.

These results support clear local head-to-head improvement over the listed existing agents. They **cannot establish that the hosted leaderboard score will exceed 2500**. One submission chance was spent for ID 56702533; the hosted 752.9 readback covers only two public games and is too early to assess its settled rating.
