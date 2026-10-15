"""Fresh paired holdout for the small-sale slot repair."""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean

from screen_market_order import BASE, CANDIDATE, GUARD, V4, factory
from fast_eval import run_adaptive

HERE = Path(__file__).resolve().parent
KAITO = HERE.parent / "ready_2500_kaito_20260930/main.py"
MAIN_SEEDS = tuple(20700019 + 241 * i for i in range(48))
PEER_SEEDS = tuple(20800011 + 251 * i for i in range(8))
rows = []
for opponent, seeds in ((V4, MAIN_SEEDS), (BASE, PEER_SEEDS), (GUARD, PEER_SEEDS), (KAITO, PEER_SEEDS)):
    for mode in (None, "small5"):
        a = run_adaptive(factory(CANDIDATE, mode), factory(opponent), seeds)
        b = run_adaptive(factory(opponent), factory(CANDIDATE, mode), seeds)
        margins = [r["money_0"] - r["money_1"] for r in a] + [r["money_1"] - r["money_0"] for r in b]
        halfwins = [r["half_win_0"] for r in a] + [1-r["half_win_0"] for r in b]
        row = {"opponent": opponent.parent.name, "mode": mode or "base", "seeds": seeds,
               "halfwins": halfwins, "margins": margins,
               "halfwin": mean(halfwins), "mean_margin": mean(margins)}
        rows.append(row)
        print(row["opponent"], row["mode"], round(row["halfwin"], 3),
              round(row["mean_margin"], 1), flush=True)
        (HERE / "MARKET_ORDER_FAST_HOLDOUT.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
