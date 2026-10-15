"""Determine whether newly screened routes can join the step-72 meta switch."""
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim" / "upstream_cppsim"))
import kagsim

names = ("rank88_c_full", "rank32_screen", "rank43_screen", "rank56_screen")
base_path = ROOT / "top20_counter_20260930" / "main.py"
seeds = [29330001 + 61*i for i in range(32)]


def at72(name, seed):
    path = HERE / "candidates" / name / "main.py"
    me = runpy.run_path(str(path))["agent"]
    other = runpy.run_path(str(base_path))["agent"]
    game = kagsim.Game(seed)
    for _ in range(72): game.step(me(game.observe(0)), other(game.observe(1)))
    obs = game.observe(0)
    own = obs["farms"][0]
    return {"physical": {k: own[k] for k in ("tiles", "farmer", "hands", "unlocked_quadrants")},
            "private": obs["private"], "cash": own["money"],
            "market": obs["market"], "town": obs["town"]}


counts = {n: {k: 0 for k in ("physical", "private", "cash", "market", "town")}
          for n in names[1:]}
cash_differences = {n: [] for n in names[1:]}
physical_mismatch_seeds = {n: [] for n in names[1:]}
for seed in seeds:
    reference = at72(names[0], seed)
    for name in names[1:]:
        current = at72(name, seed)
        for key in counts[name]: counts[name][key] += reference[key] == current[key]
        cash_differences[name].append(current["cash"] - reference["cash"])
        if reference["physical"] != current["physical"]: physical_mismatch_seeds[name].append(seed)
out = {"seeds": seeds, "counts": counts, "cash_differences": cash_differences,
       "physical_mismatch_seeds": physical_mismatch_seeds}
(HERE / "NEW_ROUTE_COMPAT_72.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(counts))
