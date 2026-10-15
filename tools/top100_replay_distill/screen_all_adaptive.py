"""Exhaustive state-aware screen of every development trajectory, both seats.

Tiny seed set is for narrowing only. It must not be reported as final validation.
"""

import argparse
import gzip
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
parser.add_argument("--start", type=int, default=22330001)
parser.add_argument("--count", type=int, default=3)
args = parser.parse_args()
seeds = [args.start + 73*i for i in range(args.count)]
manifest = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
source = (ROOT / "top20_counter_20260930" / "main.py").read_text(encoding="utf-8")
chassis_source = source.split("\nimport base64\nimport json\nimport zlib\n_R108_DATA", 1)[0]
namespace = {"__name__": "__route_screen__"}
exec(compile(chassis_source, "chassis.py", "exec"), namespace)
make_agent = namespace["make_agent"]
settings = {"hand_align": True, "weed_repair": True, "sell_lead": True,
            "front_run": False, "budget_guard": True, "room_guard": True,
            "clamp_sells": True, "dead_stock": True, "terminal_liquidation": True}
baseline_path = ROOT / "top20_counter_20260930" / "main.py"
baseline_factory = lambda: runpy.run_path(str(baseline_path))["agent"]
out = HERE / f"ADAPTIVE_ALL_{args.start}_{args.count}.json"
results = []
cache = {}
for rank_text, team in manifest["ranks"].items():
    rank = int(rank_text)
    for eid in team["development_ids"]:
        if eid not in cache:
            with gzip.open(HERE / "replays" / f"episode-{eid}-replay.json.gz", "rt", encoding="utf-8") as handle:
                cache[eid] = json.load(handle)
        replay = cache[eid]
        seat = next(i for i,a in enumerate(manifest["episodes"][eid]["agents"])
                    if a["teamId"] == team["team_id"] and a["submissionId"] == team["submission_id"])
        actions = [replay["steps"][s+1][seat].get("action") for s in range(719)]
        if not all(isinstance(a,dict) for a in actions):
            continue
        candidate_factory = lambda acts=actions: make_agent({0: acts}, **settings)
        first = run_adaptive(candidate_factory, baseline_factory, seeds)
        second = run_adaptive(baseline_factory, candidate_factory, seeds)
        margins = [r["money_0"]-r["money_1"] for r in first]
        margins += [r["money_1"]-r["money_0"] for r in second]
        results.append({"rank": rank, "episode_id": eid, "seat": seat,
                        "wins": sum(m>0 for m in margins), "losses": sum(m<0 for m in margins),
                        "mean_margin": mean(margins), "margins": margins})
        out.write_text(json.dumps({"engine": "FAST_SIM_1327_READY; development adaptive SEARCH only",
                                   "seeds": seeds, "routes_screened": len(results), "results": results},
                                  ensure_ascii=False, indent=2), encoding="utf-8")
    if rank % 10 == 0:
        top = sorted(results, key=lambda x: (x["wins"], x["mean_margin"]), reverse=True)[:3]
        print(f"rank {rank}; routes {len(results)}; top {[(x['rank'],x['episode_id'],x['wins']) for x in top]}", flush=True)
    if len(cache) > 64:
        cache.clear()
