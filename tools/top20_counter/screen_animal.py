"""Screen bounded care/feed repairs using development seeds only."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from screen_residuals import BASE, V4, factory
from fast_eval import run_adaptive

HERE = Path(__file__).resolve().parent
SEEDS = tuple(18300013 + 109 * i for i in range(12))
MODES = (
    None, "care", "care_cow", "late_care", "feed", "feed_cow",
    "care_then_feed", "feed_then_care", "cow_fert_care", "cow_fert_feed_care",
)
rows = []
for opponent in (BASE, V4):
    for mode in MODES:
        a = run_adaptive(factory(BASE, mode), factory(opponent), SEEDS)
        b = run_adaptive(factory(opponent), factory(BASE, mode), SEEDS)
        margins = [r["money_0"] - r["money_1"] for r in a] + [r["money_1"] - r["money_0"] for r in b]
        wins = [r["half_win_0"] for r in a] + [1 - r["half_win_0"] for r in b]
        row = {"opponent": opponent.parent.name, "mode": mode or "base",
               "seeds": SEEDS, "halfwin": mean(wins), "mean_margin": mean(margins),
               "margins": margins}
        rows.append(row)
        print(row["opponent"], row["mode"], round(row["halfwin"], 3),
              round(row["mean_margin"], 1), flush=True)
    (HERE / "ANIMAL_DEV_SCREEN.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
