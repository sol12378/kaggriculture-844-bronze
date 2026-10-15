"""Screen narrow sale-advance guards motivated by endgame loss inspection."""

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
MODES = (None, "no_milk", "late_no_milk", "late_no_adv", "look1", "look2", "to648", "to672", "to696", "no_front")
SEEDS = tuple(18400021 + i * 113 for i in range(8))


def factory(path, mode=None):
    def make():
        agent = runpy.run_path(str(path))["agent"]
        if mode is None:
            return agent
        g = agent.__globals__
        if mode == "no_milk":
            g["_ADV_ITEMS"] = tuple(x for x in g["_ADV_ITEMS"] if x != "MILK")
        elif mode == "look1":
            g["_ADV_LOOK"] = 1
        elif mode == "look2":
            g["_ADV_LOOK"] = 2
        elif mode == "to648":
            g["_ADV_TO"] = 648
        elif mode == "to672":
            g["_ADV_TO"] = 672
        elif mode == "to696":
            g["_ADV_TO"] = 696
        elif mode == "no_front":
            g["_ADV_FRONT"] = False
        if mode in ("late_no_milk", "late_no_adv"):
            base_items = g["_ADV_ITEMS"]
            base_to = g["_ADV_TO"]

            def wrapped(obs):
                step = int(obs["step"])
                if mode == "late_no_milk":
                    g["_ADV_ITEMS"] = tuple(x for x in base_items if x != "MILK") if step >= 672 else base_items
                else:
                    g["_ADV_TO"] = 672 if step >= 672 else base_to
                return agent(obs)

            return wrapped
        return agent

    return make


rows = []
for opponent in (BASE, V4):
    for mode in MODES:
        a = run_adaptive(factory(BASE, mode), factory(opponent), SEEDS)
        b = run_adaptive(factory(opponent), factory(BASE, mode), SEEDS)
        margins = [r["money_0"] - r["money_1"] for r in a] + [r["money_1"] - r["money_0"] for r in b]
        wins = [r["half_win_0"] for r in a] + [1-r["half_win_0"] for r in b]
        row = {"opponent": opponent.parent.name, "mode": mode or "base",
               "seeds": SEEDS, "halfwin": mean(wins), "mean_margin": mean(margins),
               "margins": margins}
        rows.append(row)
        print(row["opponent"], row["mode"], round(row["halfwin"], 3),
              round(row["mean_margin"], 1), flush=True)
    (HERE / "MARKET_DEV_SCREEN.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
