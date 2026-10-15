"""Search development-only public routes using the parity-gated fast engine."""

import gzip
import json
import runpy
import sys
from pathlib import Path
from statistics import mean

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim"))
from fast_eval import batch_fixed

manifest = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
OLD = ROOT / "top20_replay_distill_20260930" / "tapes"
CONTROLS = {
    "prior_strong_fixed": "rank20_episode115487337_seat1.json.gz",
    "prior_rank1": "rank01_episode115495283_seat0.json.gz",
}
seeds = [9130001 + 43*i for i in range(16)]
control_tapes = {}
for key, file in CONTROLS.items():
    with gzip.open(OLD / file, "rt", encoding="utf-8") as stream:
        control_tapes[key] = json.load(stream)
control_tapes["rank88_selected_fixed"] = runpy.run_path(
    str(HERE / "candidates" / "rank88_c_full" / "main.py"))["_DISTILLED_ROUTE"]

results = []
cache = {}
for rank_text, team in manifest["ranks"].items():
    rank = int(rank_text)
    for eid in team["development_ids"]:
        if eid not in cache:
            with gzip.open(HERE / "replays" / f"episode-{eid}-replay.json.gz", "rt", encoding="utf-8") as stream:
                cache[eid] = json.load(stream)
        replay = cache[eid]
        seat = next(i for i, a in enumerate(manifest["episodes"][eid]["agents"])
                    if a["submissionId"] == team["submission_id"] and a["teamId"] == team["team_id"])
        actions = [replay["steps"][s+1][seat].get("action") for s in range(719)]
        if not all(isinstance(a, dict) for a in actions):
            continue
        scores = {}
        for name, control in control_tapes.items():
            first = batch_fixed(actions, control, seeds, threads=8)
            second = batch_fixed(control, actions, seeds, threads=8)
            hw = [x["half_win_0"] for x in first] + [1-x["half_win_0"] for x in second]
            margins = [x["money_0"]-x["money_1"] for x in first]
            margins += [x["money_1"]-x["money_0"] for x in second]
            scores[name] = {"halfwin": mean(hw), "mean_margin": mean(margins)}
        results.append({"rank": rank, "episode_id": eid, "seat": seat,
                        "reward_in_source": replay["rewards"][seat], "scores": scores,
                        "pooled_halfwin": mean(s["halfwin"] for s in scores.values()),
                        "worst_halfwin": min(s["halfwin"] for s in scores.values())})
    if rank % 20 == 0:
        print("screened ranks", rank, "routes", len(results), flush=True)
    # Cap memory: retained replays only needed while both ranked seats are nearby.
    if len(cache) > 64:
        cache.clear()

results.sort(key=lambda r: (r["pooled_halfwin"], r["worst_halfwin"]), reverse=True)
output = {"engine": "FAST_SIM_1327_READY, development route search only",
          "seeds": seeds, "controls": CONTROLS, "routes": len(results), "results": results}
(HERE / "FIXED_ROUTE_SCREEN.json").write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(results[:15], ensure_ascii=False), flush=True)
