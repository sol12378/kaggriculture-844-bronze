"""Group route candidate wins by the first unlocked town shop."""

import json
import runpy
import sys
from collections import defaultdict
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim"))
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim" / "upstream_cppsim"))
import kagsim

NAMES = ("rank88_c_full", "rank88_a_basic", "rank88_d_basic", "rank88_b_basic", "rank97_basic")
results = {name: json.loads((HERE / "candidates" / name / "SCREEN_9230001_64.json").read_text(encoding="utf-8"))
           for name in NAMES}
seeds = results[NAMES[0]]["seeds"]
candidate = HERE / "candidates" / "rank88_c_full" / "main.py"
baseline = ROOT / "top20_counter_20260930" / "main.py"
shops = {}
for seed in seeds:
    a = runpy.run_path(str(candidate))["agent"]
    b = runpy.run_path(str(baseline))["agent"]
    game = kagsim.Game(seed)
    for _ in range(72):
        game.step(a(game.observe(0)), b(game.observe(1)))
    shops[seed] = (game.observe(0)["town"]["unlocked_shops"] or ["NONE"])[0]

report = {}
for name, output in results.items():
    report[name] = {}
    for baseline_name, data in output["results"].items():
        by_shop = defaultdict(list)
        for row in data["rows"]:
            by_shop[shops[row["seed"]]].append(row["margin"])
        report[name][baseline_name] = {shop: {"games": len(margins),
                                              "wins": sum(m>0 for m in margins),
                                              "mean_margin": round(mean(margins), 1)}
                                       for shop, margins in sorted(by_shop.items())}
(HERE / "SHOP_EFFECT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report, ensure_ascii=False))
