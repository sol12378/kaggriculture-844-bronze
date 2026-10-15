"""Test whether the opening price-rounding edge combines with replay repairs."""

from __future__ import annotations

import json
import runpy
from pathlib import Path
from statistics import mean

from screen_residuals import BASE, V4, repair
from fast_eval import run_adaptive

HERE = Path(__file__).resolve().parent
SEEDS = tuple(19200017 + 157 * i for i in range(32))
MODES = ("open4_only", "open4_cow_fert", "open4_cow_fert_care_water")


def factory(path, mode=None):
    def make():
        original = runpy.run_path(str(path))["agent"]
        if mode is None:
            return original

        def wrapped(obs):
            action = original(obs)
            step = int(obs["step"])
            if step in (1, 2) and isinstance(action, dict):
                market = [list(o) for o in (action.get("market") or [])]
                expected = ["BUY_PRODUCT", "WHEAT", 8] if step == 1 else ["SELL", "WHEAT", 8]
                if market and market[0] == expected:
                    market[0] = [expected[0], "WHEAT", 4]
                    action = dict(action, market=market)
            if mode == "open4_cow_fert":
                return repair(obs, action, "cow_fert")
            if mode == "open4_cow_fert_care_water":
                return repair(obs, action, "cow_fert_care_water")
            return action

        return wrapped

    return make


rows = []
for opponent in (BASE, V4):
    for mode in MODES:
        a = run_adaptive(factory(BASE, mode), factory(opponent), SEEDS)
        b = run_adaptive(factory(opponent), factory(BASE, mode), SEEDS)
        margins = [r["money_0"] - r["money_1"] for r in a] + [r["money_1"] - r["money_0"] for r in b]
        halfwins = [r["half_win_0"] for r in a] + [1-r["half_win_0"] for r in b]
        row = {"opponent": opponent.parent.name, "mode": mode, "seeds": SEEDS,
               "halfwins": halfwins, "margins": margins,
               "halfwin": mean(halfwins), "mean_margin": mean(margins)}
        rows.append(row)
        print(row["opponent"], mode, round(row["halfwin"], 3),
              round(row["mean_margin"], 1), flush=True)
        (HERE / "COMBINED_DEV.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
