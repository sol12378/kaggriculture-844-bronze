"""Confirm short-list routes from the exhaustive three-seed search on fresh seeds."""
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim"))
from fast_eval import run_adaptive

NAMES = ("rank17_screen", "rank43_screen", "rank36_screen",
         "rank32_screen", "rank30_screen", "rank56_screen")
BASES = {"submitted": ROOT / "top20_counter_20260930" / "main.py",
         "environment_meta_v1": HERE / "candidates" / "environment_meta_v1" / "main.py"}
seeds = [29330001 + 61 * i for i in range(32)]
out = {"engine": "FAST_SIM_1327_READY; adaptive live validation", "seeds": seeds, "results": {}}
target = HERE / "SHORTLIST_FRESH_29330001_32.json"
for name in NAMES:
    candidate = HERE / "candidates" / name / "main.py"
    out["results"][name] = {}
    for base_name, baseline in BASES.items():
        a = run_adaptive(lambda p=candidate: runpy.run_path(str(p))["agent"],
                         lambda p=baseline: runpy.run_path(str(p))["agent"], seeds)
        b = run_adaptive(lambda p=baseline: runpy.run_path(str(p))["agent"],
                         lambda p=candidate: runpy.run_path(str(p))["agent"], seeds)
        margins = [g["money_0"] - g["money_1"] for g in a]
        margins += [g["money_1"] - g["money_0"] for g in b]
        out["results"][name][base_name] = {
            "wins": sum(m > 0 for m in margins), "losses": sum(m < 0 for m in margins),
            "ties": sum(m == 0 for m in margins),
            "mean_margin": round(sum(margins) / len(margins), 2)}
        print(name, base_name, out["results"][name][base_name], flush=True)
        target.write_text(json.dumps(out, indent=2), encoding="utf-8")
