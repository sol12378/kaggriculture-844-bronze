"""Screen stable sale-slot repairs on non-mirrored opening matchups."""

from __future__ import annotations

import json
import runpy
from pathlib import Path
from statistics import mean

from screen_residuals import BASE, GUARD, V4
from fast_eval import run_adaptive

HERE = Path(__file__).resolve().parent
CANDIDATE = HERE / "candidate_conditional/main.py"
SEEDS = tuple(20500011 + 223 * i for i in range(24))
PEER_SEEDS = tuple(20600003 + 229 * i for i in range(8))
MODES = (None, "small1", "small3", "small5", "value_sort")


def factory(path, mode=None):
    def make():
        original = runpy.run_path(str(path))["agent"]
        if mode is None:
            return original
        g = original.__globals__

        def wrapped(obs):
            action = original(obs)
            if not isinstance(action, dict) or int(obs["step"]) < 144:
                return action
            if g.get("_COND_MIRROR", {}).get(int(obs["player"])):
                return action
            market = [list(o) for o in (action.get("market") or [])]
            if len(market) < 2 or any(not o or o[0] != "SELL" or len(o) < 3 for o in market):
                return action
            if mode == "value_sort":
                prices = obs["market"]["prices"]
                reordered = sorted(market, key=lambda o: -max(0, int(o[2])) * int(prices.get(o[1], 0)))
            else:
                cap = int(mode[-1])
                first = market[0]
                if int(first[2]) > cap or not any(int(o[2]) >= 10 for o in market[1:]):
                    return action
                reordered = market[1:] + [first]
            return dict(action, market=reordered) if reordered != market else action

        return wrapped

    return make


if __name__ == "__main__":
    rows = []
    for opponent, seeds in ((V4, SEEDS), (BASE, PEER_SEEDS), (GUARD, PEER_SEEDS)):
        for mode in MODES:
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
            (HERE / "MARKET_ORDER_DEV.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
