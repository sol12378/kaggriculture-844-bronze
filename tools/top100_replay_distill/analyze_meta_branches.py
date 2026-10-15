"""Audit that environment routing uses public features and identify winning branches."""
import json
import runpy
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim" / "upstream_cppsim"))
import kagsim

league = json.loads((HERE / "META_VALIDATION_28330001_32.json").read_text(encoding="utf-8"))
out = {}
for opponent in ("rank88_c_full", "rank97_basic", "submitted"):
    rows = league["pairs"][f"environment_meta_v1|{opponent}"]
    margins = {(r["seed"], r["seat_a"]): r["margin_a"] for r in rows}
    opponent_path = (HERE / "candidates" / opponent / "main.py") if opponent != "submitted" else (ROOT / "top20_counter_20260930" / "main.py")
    groups = defaultdict(list)
    for seed in league["seeds"]:
        for seat in (0, 1):
            me = runpy.run_path(str(HERE / "candidates" / "environment_meta_v1" / "main.py"))["agent"]
            rival = runpy.run_path(str(opponent_path))["agent"]
            game = kagsim.Game(seed)
            agents = (me, rival) if seat == 0 else (rival, me)
            for _ in range(72): game.step(agents[0](game.observe(0)), agents[1](game.observe(1)))
            obs = game.observe(seat)
            shop = obs["town"]["unlocked_shops"][0]
            rival_farm = obs["farms"][1-seat]
            sheep = sum(t.get("animal") == "SHEEP" for row in rival_farm["tiles"]
                        for t in row if isinstance(t, dict) and t.get("kind") == "PASTURE")
            route = "rank88c" if shop in ("PIZZA_SHOP", "BRUNCH_SPOT") and sheep < 3 else "rank97"
            groups[(shop, route)].append(margins[(seed, seat)])
    out[opponent] = {f"{shop}|{route}": {"games": len(v), "wins": sum(x > 0 for x in v),
                                             "mean_margin": round(sum(v)/len(v))}
                     for (shop, route), v in groups.items()}
print(json.dumps(out, indent=2))
(HERE / "META_BRANCH_AUDIT.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
