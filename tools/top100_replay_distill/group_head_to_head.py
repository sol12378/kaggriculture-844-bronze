"""Attribute official candidate-vs-candidate outcomes to first unlocked shop."""

import json
import runpy
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim" / "upstream_cppsim"))
import kagsim

path = HERE / "candidates" / "shop_hybrid_four" / "OFFICIAL_rank97_17330001_24.json"
data = json.loads(path.read_text(encoding="utf-8"))
seeds = data["seeds"]
shops = {}
for seed in seeds:
    game = kagsim.Game(seed)
    a = runpy.run_path(str(HERE / "candidates" / "shop_hybrid_four" / "main.py"))["agent"]
    b = runpy.run_path(str(HERE / "candidates" / "rank97_basic" / "main.py"))["agent"]
    for _ in range(72):
        game.step(a(game.observe(0)), b(game.observe(1)))
    shops[seed] = game.observe(0)["town"]["unlocked_shops"][0]

by_shop = defaultdict(list)
for row in data["rows"]:
    by_shop[shops[row["seed"]]].append(row["candidate_reward"] - row["baseline_reward"])
result = {shop: {"games": len(margins), "wins": sum(m>0 for m in margins),
                 "mean_margin": round(mean(margins), 1), "margins": margins}
          for shop, margins in sorted(by_shop.items())}
(HERE / "HEADTOHEAD_SHOPS.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: {j:v for j,v in row.items() if j!='margins'} for k,row in result.items()}))
