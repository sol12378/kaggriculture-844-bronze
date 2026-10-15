"""Search narrow top-20 replay inspired repairs on a separate seed panel."""

from __future__ import annotations

import copy
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
MAX_AGE = {"WHEAT": 4, "CARROT": 3, "MELON": 12}
MODES = ("cow_fert", "all_fert", "animal_harvest", "crop_harvest", "water", "fert_harvest", "all_local")
SEEDS = tuple(18200011 + i * 97 for i in range(12))


def repair(obs, action, mode):
    if not isinstance(action, dict):
        return action
    farm = obs["farms"][int(obs["player"])]
    positions = [farm["farmer"], *(farm.get("hands") or [])]
    commands = [action.get("farmer"), *(action.get("hands") or [])]
    if len(positions) != len(commands):
        return action
    out = None
    handled = set()
    for actor, (pos, command) in enumerate(zip(positions, commands)):
        if command != ["PASS"] or tuple(pos) in handled:
            continue
        x, y = pos
        tile = farm["tiles"][y][x]
        if not isinstance(tile, dict):
            continue
        op = None
        if tile.get("animal"):
            animal = tile.get("animal")
            invs = (obs.get("private") or {}).get("inventories") or []
            wheat = actor < len(invs) and invs[actor].get("WHEAT", 0) > 0
            can_feed = not tile.get("fed_today") and wheat
            can_care = not tile.get("cared_today")
            if mode == "care" and can_care:
                op = "CARE"
            elif mode == "care_cow" and animal == "COW" and can_care:
                op = "CARE"
            elif mode == "late_care" and int(obs.get("hour", 0)) >= 18 and can_care:
                op = "CARE"
            elif mode == "feed" and can_feed:
                op = "FEED"
            elif mode == "feed_cow" and animal == "COW" and can_feed:
                op = "FEED"
            elif mode == "care_then_feed":
                op = "CARE" if can_care else "FEED" if can_feed else None
            elif mode == "feed_then_care":
                op = "FEED" if can_feed else "CARE" if can_care else None
            elif mode in ("cow_fert_care", "cow_fert_feed_care", "cow_fert_care_water"):
                if mode == "cow_fert_feed_care" and can_feed:
                    op = "FEED"
                elif can_care:
                    op = "CARE"
                elif animal == "COW" and tile.get("fertilizer_available"):
                    op = "COLLECT_FERTILIZER"
            elif mode in ("animal_harvest", "all_local") and tile.get("yield_units", 0) > 0:
                op = "HARVEST"
            elif mode in ("cow_fert", "cow_fert_water", "all_fert", "fert_harvest", "all_local") and tile.get("fertilizer_available"):
                if mode not in ("cow_fert", "cow_fert_water") or tile.get("animal") == "COW":
                    op = "COLLECT_FERTILIZER"
        elif tile.get("kind") == "PLANT":
            crop = tile.get("crop")
            if mode in ("water", "cow_fert_water", "cow_fert_care_water", "all_local") and not tile.get("watered_today"):
                op = "WATER"
            elif mode in ("crop_harvest", "fert_harvest", "all_local") and tile.get("yield_units", 0) > 0:
                age = int(obs.get("day", 0)) - int(tile.get("planted_day", 0))
                if crop not in MAX_AGE or age >= MAX_AGE[crop]:
                    op = "HARVEST"
        if op is None:
            continue
        if out is None:
            out = copy.deepcopy(action)
        if actor == 0:
            out["farmer"] = [op]
        else:
            out["hands"][actor - 1] = [op]
        handled.add(tuple(pos))
    return out if out is not None else action


def factory(path, mode=None):
    def make():
        original = runpy.run_path(str(path))["agent"]
        if mode is None:
            return original

        def wrapped(obs):
            return repair(obs, original(obs), mode)

        return wrapped

    return make


def score(mode, opponent):
    a = run_adaptive(factory(BASE, mode), factory(opponent), SEEDS)
    b = run_adaptive(factory(opponent), factory(BASE, mode), SEEDS)
    margins = [r["money_0"] - r["money_1"] for r in a] + [r["money_1"] - r["money_0"] for r in b]
    halfwins = [r["half_win_0"] for r in a] + [1 - r["half_win_0"] for r in b]
    return {"mode": mode or "base", "opponent": opponent.name, "seeds": SEEDS,
            "mean_margin": mean(margins), "halfwin": mean(halfwins),
            "margins": margins, "halfwins": halfwins}


if __name__ == "__main__":
    rows = []
    for opponent in (BASE, V4, GUARD):
        for mode in ((None,) + MODES):
            row = score(mode, opponent)
            rows.append(row)
            print(opponent.parent.name, row["mode"], round(row["halfwin"], 3),
                  round(row["mean_margin"], 1), flush=True)
        (HERE / "RESIDUAL_DEV_SCREEN.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
