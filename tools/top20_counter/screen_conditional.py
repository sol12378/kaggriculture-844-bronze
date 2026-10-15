"""Hold out a conditional market and worker controller against several peers."""

from __future__ import annotations

import json
import runpy
from pathlib import Path
from statistics import mean

from screen_residuals import BASE, GUARD, V4, repair
from fast_eval import run_adaptive

HERE = Path(__file__).resolve().parent
KAITO = HERE.parent / "ready_2500_kaito_20260930/main.py"
MAIN_SEEDS = tuple(19400009 + 163 * i for i in range(32))
PEER_SEEDS = tuple(19500007 + 173 * i for i in range(8))


def factory(path, mode=None):
    def make():
        original = runpy.run_path(str(path))["agent"]
        if mode is None:
            return original
        mirror = False

        def wrapped(obs):
            nonlocal mirror
            action = original(obs)
            step = int(obs["step"])
            if step in (1, 2) and isinstance(action, dict):
                market = [list(o) for o in (action.get("market") or [])]
                if step == 1 and market and market[0] == ["BUY_PRODUCT", "WHEAT", 8]:
                    mirror = True
                    market[0] = ["BUY_PRODUCT", "WHEAT", 4]
                    action = dict(action, market=market)
                elif step == 2 and mirror and market and market[0] == ["SELL", "WHEAT", 8]:
                    market[0] = ["SELL", "WHEAT", 4]
                    action = dict(action, market=market)
            if mirror or mode == "open4_only":
                return action
            return repair(obs, action, "cow_fert_care_water")

        return wrapped

    return make


rows = []
for opponent, seeds in ((BASE, MAIN_SEEDS), (V4, MAIN_SEEDS), (GUARD, PEER_SEEDS), (KAITO, PEER_SEEDS)):
    for mode in ("open4_only", "conditional"):
        a = run_adaptive(factory(BASE, mode), factory(opponent), seeds)
        b = run_adaptive(factory(opponent), factory(BASE, mode), seeds)
        margins = [r["money_0"] - r["money_1"] for r in a] + [r["money_1"] - r["money_0"] for r in b]
        halfwins = [r["half_win_0"] for r in a] + [1-r["half_win_0"] for r in b]
        row = {"opponent": opponent.parent.name, "mode": mode, "seeds": seeds,
               "halfwins": halfwins, "margins": margins,
               "halfwin": mean(halfwins), "mean_margin": mean(margins)}
        rows.append(row)
        print(row["opponent"], mode, round(row["halfwin"], 3),
              round(row["mean_margin"], 1), flush=True)
        (HERE / "CONDITIONAL_FAST_HOLDOUT.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
