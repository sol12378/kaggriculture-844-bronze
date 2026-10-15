"""Screen the unequal-opening wheat round trip against the local V4 policy."""

from __future__ import annotations

import json
import runpy
from pathlib import Path
from statistics import mean

from screen_residuals import V4
from fast_eval import run_adaptive

HERE = Path(__file__).resolve().parent
BASE = HERE / "candidate_conditional/main.py"
SEEDS = tuple(20400013 + 211 * i for i in range(12))
UNITS = (0, 8, 12, 16, 20, 24, 30, 36, 42, 50, 60)


def factory(path, units=None):
    def make():
        original = runpy.run_path(str(path))["agent"]
        if units is None or units == 30:
            return original

        def wrapped(obs):
            action = original(obs)
            step = int(obs["step"])
            if step not in (1, 2) or not isinstance(action, dict):
                return action
            market = [list(o) for o in (action.get("market") or [])]
            expected = ["BUY_PRODUCT", "WHEAT", 30] if step == 1 else ["SELL", "WHEAT", 30]
            if not market or market[0] != expected:
                return action
            market = ([[expected[0], "WHEAT", units]] if units else []) + market[1:]
            return dict(action, market=market)

        return wrapped

    return make


rows = []
for units in UNITS:
    a = run_adaptive(factory(BASE, units), factory(V4), SEEDS)
    b = run_adaptive(factory(V4), factory(BASE, units), SEEDS)
    margins = [r["money_0"] - r["money_1"] for r in a] + [r["money_1"] - r["money_0"] for r in b]
    halfwins = [r["half_win_0"] for r in a] + [1-r["half_win_0"] for r in b]
    row = {"attack_units": units, "seeds": SEEDS,
           "halfwins": halfwins, "margins": margins,
           "halfwin": mean(halfwins), "mean_margin": mean(margins)}
    rows.append(row)
    print(units, round(row["halfwin"], 3), round(row["mean_margin"], 1), flush=True)
    (HERE / "V4_ATTACK_DEV.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
