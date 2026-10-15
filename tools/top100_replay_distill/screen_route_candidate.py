"""Paired fast-simulator search screen against submitted and prior agents."""

import argparse
import json
import runpy
import sys
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim"))
from fast_eval import run_adaptive

parser = argparse.ArgumentParser()
parser.add_argument("candidate")
parser.add_argument("--start", type=int, default=8130001)
parser.add_argument("--count", type=int, default=12)
args = parser.parse_args()
candidate_path = HERE / "candidates" / args.candidate / "main.py"
assert candidate_path.exists()
SEEDS = [args.start + 61 * i for i in range(args.count)]
BASES = {"submitted": ROOT / "top20_counter_20260930" / "main.py",
         "v4": ROOT / "submission_ready_20260930" / "main.py"}


def factory(path):
    return lambda: runpy.run_path(str(path))["agent"]


results = {}
for name, path in BASES.items():
    first = run_adaptive(factory(candidate_path), factory(path), SEEDS)
    second = run_adaptive(factory(path), factory(candidate_path), SEEDS)
    rows = []
    for seat, games in ((0, first), (1, second)):
        for game in games:
            cand = game[f"money_{seat}"]
            base = game[f"money_{1-seat}"]
            rows.append({"seed": game["seed"], "seat": seat, "candidate": cand,
                         "baseline": base, "margin": cand-base, "halfwin": .5 if cand==base else int(cand>base)})
    results[name] = {"wins": sum(r["margin"]>0 for r in rows),
                     "losses": sum(r["margin"]<0 for r in rows),
                     "ties": sum(r["margin"]==0 for r in rows),
                     "mean_margin": mean(r["margin"] for r in rows),
                     "median_margin": sorted(r["margin"] for r in rows)[len(rows)//2],
                     "rows": rows}
    print(name, results[name]["wins"], results[name]["losses"], round(results[name]["mean_margin"], 1), flush=True)

out = {"candidate": args.candidate, "engine": "FAST_SIM_1327_READY, search only",
       "seeds": SEEDS, "results": results}
(HERE / "candidates" / args.candidate / f"SCREEN_{args.start}_{args.count}.json").write_text(
    json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
