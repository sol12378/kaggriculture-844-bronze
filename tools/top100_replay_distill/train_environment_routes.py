"""Measure public environment features and live route outcomes on development seeds."""
import argparse
import json
import runpy
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim"))
from fast_eval import _require_ready
import kagsim

ROUTES = ("rank88_c_full", "rank88_a_basic", "rank88_b_basic", "rank97_basic")
OPPONENTS = {
    "submitted": ROOT / "top20_counter_20260930" / "main.py",
    "v4": ROOT / "submission_ready_20260930" / "main.py",
    "ready2500": ROOT / "ready_2500_final_20260930" / "main.py",
    "second_meta": ROOT / "second_meta_agent_20260930" / "main.py",
    "rank88c": HERE / "candidates" / "rank88_c_full" / "main.py",
    "rank97": HERE / "candidates" / "rank97_basic" / "main.py",
}


def feature(obs):
    player = int(obs["player"])
    opponent = obs["farms"][1 - player]
    mine = obs["farms"][player]
    crops, animals = Counter(), Counter()
    for row in opponent["tiles"]:
        for tile in row:
            if isinstance(tile, dict):
                if tile.get("kind") == "PLANT": crops[tile.get("crop")] += 1
                elif tile.get("kind") == "PASTURE": animals[tile.get("animal")] += 1
    shops = obs.get("town", {}).get("unlocked_shops", [])
    return {"shop": shops[0] if shops else "NONE",
            "rival_cash": opponent.get("money", 0), "my_cash": mine.get("money", 0),
            "rival_hands": len(opponent.get("hands", [])),
            "rival_crops": dict(crops), "rival_animals": dict(animals),
            "market_keys": list(obs.get("market", {})) if isinstance(obs.get("market"), dict) else []}


def main():
    _require_ready()
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=26330001)
    parser.add_argument("--count", type=int, default=16)
    args = parser.parse_args()
    seeds = [args.start + 61 * i for i in range(args.count)]
    rows = []
    for route in ROUTES:
        route_path = HERE / "candidates" / route / "main.py"
        for opponent, opponent_path in OPPONENTS.items():
            for seed in seeds:
                for seat in (0, 1):
                    me = runpy.run_path(str(route_path))["agent"]
                    rival = runpy.run_path(str(opponent_path))["agent"]
                    agents = (me, rival) if seat == 0 else (rival, me)
                    game = kagsim.Game(seed)
                    context = None
                    while not game.done:
                        if game.observe(seat)["step"] == 72:
                            context = feature(game.observe(seat))
                        game.step(agents[0](game.observe(0)), agents[1](game.observe(1)))
                    margin = game.reward(seat) - game.reward(1 - seat)
                    rows.append({"route": route, "opponent": opponent, "seed": seed,
                                 "seat": seat, "margin": margin,
                                 "halfwin": .5 if margin == 0 else int(margin > 0),
                                 "context": context})
            wins = sum(r["halfwin"] for r in rows if r["route"] == route and r["opponent"] == opponent)
            print(route, opponent, wins, "/", 2 * len(seeds), flush=True)
            (HERE / f"ENV_TRAIN_{args.start}_{args.count}.json").write_text(
                json.dumps({"seeds": seeds, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__": main()
