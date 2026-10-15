"""Verify selected routes reach equivalent own physical states at step 72."""

import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim" / "upstream_cppsim"))
import kagsim

seeds = [15330001 + 61*i for i in range(64)]
base_path = ROOT / "top20_counter_20260930" / "main.py"
paths = {name: HERE / "candidates" / name / "main.py" for name in
         ("rank88_c_full", "rank97_basic", "rank88_a_basic", "rank88_b_basic")}


def state_at_72(path, seed):
    agent = runpy.run_path(str(path))["agent"]
    baseline = runpy.run_path(str(base_path))["agent"]
    game = kagsim.Game(seed)
    for _ in range(72):
        game.step(agent(game.observe(0)), baseline(game.observe(1)))
    obs = game.observe(0)
    return {"farm": obs["farms"][0], "private": obs["private"],
            "market": obs["market"], "town": obs["town"]}


counts = {name: {"farm_equal": 0, "physical_equal": 0, "cash_equal": 0, "market_equal": 0, "shops_equal": 0}
          for name in paths if name != "rank88_c_full"}
examples = []
for seed in seeds:
    ref = state_at_72(paths["rank88_c_full"], seed)
    for name, path in paths.items():
        if name == "rank88_c_full":
            continue
        other = state_at_72(path, seed)
        a, b = ref["farm"], other["farm"]
        counts[name]["farm_equal"] += a == b
        counts[name]["physical_equal"] += (a["farmer"] == b["farmer"] and a["hands"] == b["hands"]
                                           and a["tiles"] == b["tiles"] and ref["private"] == other["private"])
        counts[name]["cash_equal"] += a["money"] == b["money"]
        counts[name]["market_equal"] += ref["market"] == other["market"]
        counts[name]["shops_equal"] += ref["town"] == other["town"]
        if len(examples) < 8 and a != b:
            examples.append({"seed": seed, "other": name,
                             "cash_a": a["money"], "cash_b": b["money"],
                             "positions_equal": a["farmer"] == b["farmer"] and a["hands"] == b["hands"]})
out = {"seeds": seeds, "counts": counts, "difference_examples": examples}
(HERE / "SWITCH_COMPAT_72.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(counts))
