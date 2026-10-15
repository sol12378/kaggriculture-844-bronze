"""Inspect rank32 route gains by public first shop on development seeds."""
import json
import runpy
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim" / "upstream_cppsim"))
import kagsim

path = HERE / "RANK32_DEV_27330001_32.json"
data = json.loads(path.read_text(encoding="utf-8"))
shops = {}
for seed in data["seeds"]:
    me = runpy.run_path(str(HERE / "candidates" / "rank32_screen" / "main.py"))["agent"]
    rival = runpy.run_path(str(ROOT / "top20_counter_20260930" / "main.py"))["agent"]
    game = kagsim.Game(seed)
    for _ in range(72): game.step(me(game.observe(0)), rival(game.observe(1)))
    shops[seed] = game.observe(0)["town"]["unlocked_shops"][0]

out = {}
for key, rows in data["pairs"].items():
    if not key.startswith("rank32_screen|"): continue
    by_shop = defaultdict(list)
    for r in rows: by_shop[shops[r["seed"]]].append(r["margin_a"])
    out[key] = {shop: {"games": len(values), "wins": sum(v > 0 for v in values),
                       "mean_margin": round(sum(values)/len(values))}
                for shop, values in by_shop.items()}
print(json.dumps(out, indent=2))
(HERE / "RANK32_SHOP_EFFECT.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
