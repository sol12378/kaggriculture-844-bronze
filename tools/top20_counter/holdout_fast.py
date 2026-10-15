"""Independent seeded holdout for replay-derived local repairs."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from screen_residuals import BASE, V4, factory
from fast_eval import run_adaptive

HERE = Path(__file__).resolve().parent
SEEDS = tuple(19100003 + 137 * i for i in range(48))
MODES = ("cow_fert", "cow_fert_care", "cow_fert_water", "cow_fert_care_water")
rows = []
for mode in MODES:
    for opponent in (BASE, V4):
        a = run_adaptive(factory(BASE, mode), factory(opponent), SEEDS)
        b = run_adaptive(factory(opponent), factory(BASE, mode), SEEDS)
        margins = [r["money_0"] - r["money_1"] for r in a] + [r["money_1"] - r["money_0"] for r in b]
        halfwins = [r["half_win_0"] for r in a] + [1-r["half_win_0"] for r in b]
        row = {"mode": mode, "opponent": opponent.parent.name, "seeds": SEEDS,
               "halfwins": halfwins, "margins": margins,
               "halfwin": mean(halfwins), "mean_margin": mean(margins)}
        rows.append(row)
        print(mode, row["opponent"], round(row["halfwin"], 3),
              round(row["mean_margin"], 1), flush=True)
        (HERE / "RESIDUAL_FAST_HOLDOUT.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
