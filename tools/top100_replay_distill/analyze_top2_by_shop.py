"""Compare the two leading compatible routes by public first-shop environment."""
import json
import runpy
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim" / "upstream_cppsim"))
import kagsim
from aggregate_two_families import margins_initial, margins_second

routes = ("rank32_plus8_front97", "environment_meta_front_97")
opponents = ("rank95_front97", "rank88_c_full", "rank97_plus4", "submitted", "second_meta")
seeds = [36330001 + 67*i for i in range(24)] + [38330001 + 67*i for i in range(32)]
shop_by_seed = {}
for seed in seeds:
    me = runpy.run_path(str(HERE / "candidates" / "rank88_c_full" / "main.py"))["agent"]
    rival = runpy.run_path(str(ROOT / "top20_counter_20260930" / "main.py"))["agent"]
    game = kagsim.Game(seed)
    for _ in range(72): game.step(me(game.observe(0)), rival(game.observe(1)))
    shop_by_seed[seed] = game.observe(0)["town"]["unlocked_shops"][0]

groups = defaultdict(list)
for opponent in opponents:
    a = {**margins_initial(routes[0], opponent), **margins_second(routes[0], opponent)}
    b = {**margins_initial(routes[1], opponent), **margins_second(routes[1], opponent)}
    assert a.keys() == b.keys()
    for (seed, seat), margin32 in a.items():
        margin_meta = b[(seed,seat)]
        row = {"seed": seed, "seat": seat, "opponent": opponent, "shop": shop_by_seed[seed],
               "win_delta": int(margin32 > 0) - int(margin_meta > 0),
               "margin_delta": margin32 - margin_meta}
        groups[("shop", row["shop"])].append(row)
        groups[("shop_opponent", row["shop"], opponent)].append(row)
        groups[("opponent", opponent)].append(row)

report = {}
for key, rows in groups.items():
    report["|".join(key)] = {"games": len(rows),
        "rank32_extra_wins": sum(r["win_delta"] for r in rows),
        "rank32_mean_margin_gain": round(sum(r["margin_delta"] for r in rows)/len(rows)),
        "first_family_extra_wins": sum(r["win_delta"] for r in rows if r["seed"]<38000000),
        "second_family_extra_wins": sum(r["win_delta"] for r in rows if r["seed"]>38000000)}
(HERE / "TOP2_SHOP_EFFECT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
for key in sorted(report):
    if key.startswith("shop|"): print(key, report[key])
