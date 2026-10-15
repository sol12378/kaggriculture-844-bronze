"""Development-free holdout matchup against 100 top-ranked action trajectories.

Opponents replay observed actions, so this is a diagnostic, not a live-policy test.
"""

import argparse
import gzip
import json
import runpy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim"))
from fast_eval import run_adaptive

parser = argparse.ArgumentParser()
parser.add_argument("candidate")
parser.add_argument("--first-rank", type=int, default=1)
parser.add_argument("--last-rank", type=int, default=100)
args = parser.parse_args()
assert 1 <= args.first_rank <= args.last_rank <= 100
candidate = HERE / "candidates" / args.candidate / "main.py"
baseline = ROOT / "top20_counter_20260930" / "main.py"
manifest = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
rows = []
out = HERE / "candidates" / args.candidate / f"HOLDOUT_TOP{args.first_rank}_{args.last_rank}.json"


def agent_factory(path):
    return lambda: runpy.run_path(str(path))["agent"]


for rank in range(args.first_rank, args.last_rank + 1):
    team = manifest["ranks"][str(rank)]
    eid = team["validation_ids"][0]
    with gzip.open(HERE / "replays" / f"episode-{eid}-replay.json.gz", "rt", encoding="utf-8") as stream:
        replay = json.load(stream)
    seat = next(i for i, a in enumerate(manifest["episodes"][eid]["agents"])
                if a["submissionId"] == team["submission_id"] and a["teamId"] == team["team_id"])
    tape = [replay["steps"][s+1][seat].get("action") or {"farmer":["PASS"], "hands":[], "market":[]}
            for s in range(719)]

    def tape_factory():
        def policy(obs):
            return tape[int(obs["step"])]
        return policy

    seed = 9530001 + 71*rank
    result = {"rank": rank, "episode_id": eid, "new_seed": seed}
    for name, path in (("candidate", candidate), ("submitted", baseline)):
        first = run_adaptive(agent_factory(path), tape_factory, [seed])[0]
        second = run_adaptive(tape_factory, agent_factory(path), [seed])[0]
        result[name] = {"seat0_margin": first["money_0"]-first["money_1"],
                        "seat1_margin": second["money_1"]-second["money_0"]}
    rows.append(result)
    out.write_text(json.dumps({"engine": "FAST_SIM_1327_READY; held-out fixed action tapes, not live opponents",
                               "candidate": args.candidate, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    if rank % 10 == 0:
        cw = sum(m>0 for r in rows for m in r["candidate"].values())
        bw = sum(m>0 for r in rows for m in r["submitted"].values())
        print(f"rank {rank}: candidate {cw} wins, submitted {bw} wins / {2*len(rows)}", flush=True)
