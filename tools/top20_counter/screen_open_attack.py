"""Search the mirror opening's wheat price-pressure quantity."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922/fast_sim"))
from fast_eval import run_adaptive  # noqa: E402

BASE = ROOT / "ready_2500_final_20260930/main.py"
V4 = ROOT / "submission_ready_20260930/main.py"
GUARD = ROOT / "kg401_synergy_20260923/public_sources/llccqq_adaptive_shop_guard_v1/output/main.py"
SEEDS = tuple(18500007 + 149 * i for i in range(12))
UNITS = (0, 4, 8, 12, 16, 24, 32, 48)


def factory(path, units=None):
    def make():
        original = runpy.run_path(str(path))["agent"]
        if units is None or units == 8:
            return original

        def wrapped(obs):
            step = int(obs["step"])
            action = original(obs)
            if step not in (1, 2) or not isinstance(action, dict):
                return action
            market = [list(o) for o in (action.get("market") or [])]
            if step == 1 and market and market[0] == ["BUY_PRODUCT", "WHEAT", 8]:
                market = ([["BUY_PRODUCT", "WHEAT", units]] if units else []) + market[1:]
            elif step == 2 and market and market[0] == ["SELL", "WHEAT", 8]:
                market = [["SELL", "WHEAT", units]] + market[1:] if units else market[1:]
            else:
                return action
            return dict(action, market=market)

        return wrapped

    return make


rows = []
for opponent in (BASE, V4):
    for units in UNITS:
        a = run_adaptive(factory(BASE, units), factory(opponent), SEEDS)
        b = run_adaptive(factory(opponent), factory(BASE, units), SEEDS)
        margins = [r["money_0"] - r["money_1"] for r in a] + [r["money_1"] - r["money_0"] for r in b]
        halfwins = [r["half_win_0"] for r in a] + [1-r["half_win_0"] for r in b]
        row = {"opponent": opponent.parent.name, "attack_units": units, "seeds": SEEDS,
               "halfwins": halfwins, "margins": margins,
               "halfwin": mean(halfwins), "mean_margin": mean(margins)}
        rows.append(row)
        print(row["opponent"], units, round(row["halfwin"], 3),
              round(row["mean_margin"], 1), flush=True)
        (HERE / "OPEN_ATTACK_DEV.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
