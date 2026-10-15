"""Official 1.32.7 file-loader comparison on seeds unused during search."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path
from statistics import mean

from kaggle_environments import make

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CANDIDATE = HERE / "candidate_cow_fert_care_water/main.py"
BASE = ROOT / "ready_2500_final_20260930/main.py"
V4 = ROOT / "submission_ready_20260930/main.py"
GUARD = ROOT / "kg401_synergy_20260923/public_sources/llccqq_adaptive_shop_guard_v1/output/main.py"
KAITO = ROOT / "ready_2500_kaito_20260930/main.py"
MAIN_SEEDS = tuple(19700003 + 127 * i for i in range(24))
PEER_SEEDS = tuple(19800019 + 137 * i for i in range(8))
CASES = (
    ("candidate_vs_parent", CANDIDATE, BASE, MAIN_SEEDS),
    ("candidate_vs_v4", CANDIDATE, V4, MAIN_SEEDS),
    ("parent_vs_v4_control", BASE, V4, MAIN_SEEDS),
    ("candidate_vs_guard", CANDIDATE, GUARD, PEER_SEEDS),
    ("candidate_vs_kaito", CANDIDATE, KAITO, PEER_SEEDS),
)
rows = []
for label, test_agent, opponent, seeds in CASES:
    for seed in seeds:
        pair = []
        for seat in (0, 1):
            players = [str(test_agent), str(opponent)] if seat == 0 else [str(opponent), str(test_agent)]
            log = io.StringIO()
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
                final = env.run(players)[-1]
            first = env.steps[1][seat].get("action")
            active = sum(
                isinstance(action, dict)
                and (bool(action.get("market")) or action.get("farmer") != ["PASS"] or bool(action.get("hands")))
                for action in (step[seat].get("action") for step in env.steps[1:])
            )
            row = {
                "case": label, "seed": seed, "seat": seat,
                "reward": final[seat]["reward"], "opponent_reward": final[1 - seat]["reward"],
                "status": final[seat]["status"], "opponent_status": final[1 - seat]["status"],
                "steps": len(env.steps), "active_turns": active,
                "first_action": first if len(rows) == 0 else None,
                "loader_fallback": not isinstance(first, dict) or "__raw_path__" in first,
                "log_excerpt": log.getvalue()[:200],
            }
            assert row["status"] == "DONE" and row["steps"] == 720, row
            assert row["active_turns"] > 600 and not row["loader_fallback"], row
            rows.append(row)
            pair.append(row["reward"] - row["opponent_reward"])
        print(label, seed, pair, flush=True)
        (HERE / "OFFICIAL_FRESH_GAMES.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

summary = []
for label, *_ in CASES:
    selected = [row for row in rows if row["case"] == label]
    margins = [r["reward"] - r["opponent_reward"] for r in selected]
    halfwins = [0.5 if m == 0 else float(m > 0) for m in margins]
    summary.append({"case": label, "games": len(selected), "seed_pairs": len(selected) // 2,
                    "wins": sum(m > 0 for m in margins), "losses": sum(m < 0 for m in margins),
                    "ties": sum(m == 0 for m in margins),
                    "halfwin": mean(halfwins), "mean_margin": mean(margins)})
report = {"engine": "kaggle-environments 1.32.7", "loader": "file paths in env.run",
          "search_seed_overlap": False, "summary": summary,
          "submission_performed": False}
(HERE / "OFFICIAL_FRESH_SUMMARY.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(summary), flush=True)
