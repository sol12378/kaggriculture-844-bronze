"""Confirm selected candidates in the path-loaded official 1.32.7 engine."""

import argparse
import contextlib
import io
import json
import multiprocessing as mp
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASES = {"submitted": ROOT / "top20_counter_20260930" / "main.py",
         "v4": ROOT / "submission_ready_20260930" / "main.py",
         "ready2500": ROOT / "ready_2500_final_20260930" / "main.py",
         "meta_candidate": ROOT / "second_meta_agent_20260930" / "main.py",
         "rank97": HERE / "candidates" / "rank97_basic" / "main.py",
         "rank88c": HERE / "candidates" / "rank88_c_full" / "main.py"}


def one(task):
    candidate_path, baseline_path, seat, seed = task
    from kaggle_environments import make
    agents = [str(candidate_path), str(baseline_path)] if seat == 0 else [str(baseline_path), str(candidate_path)]
    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        final = env.run(agents)[-1]
    return {"seed": seed, "seat": seat, "candidate_reward": final[seat]["reward"],
            "baseline_reward": final[1-seat]["reward"],
            "candidate_status": final[seat]["status"], "baseline_status": final[1-seat]["status"],
            "steps": len(env.steps), "log_excerpt": output.getvalue()[:200]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("--baseline", choices=BASES, default="submitted")
    parser.add_argument("--start", type=int, default=8330001)
    parser.add_argument("--count", type=int, default=12)
    args = parser.parse_args()
    candidate = HERE / "candidates" / args.candidate / "main.py"
    assert candidate.is_file(), candidate
    baseline = BASES[args.baseline]
    seeds = [args.start + 67*i for i in range(args.count)]
    tasks = [(candidate, baseline, seat, seed) for seed in seeds for seat in (0, 1)]
    rows = []
    output = HERE / "candidates" / args.candidate / f"OFFICIAL_{args.baseline}_{args.start}_{args.count}.json"
    with mp.Pool(4, maxtasksperchild=1) as pool:
        for row in pool.imap_unordered(one, tasks):
            rows.append(row)
            output.write_text(json.dumps({"engine": "official kaggle_environments 1.32.7 path loader",
                                          "candidate": args.candidate, "baseline": args.baseline,
                                          "seeds": seeds, "rows": rows}, indent=2), encoding="utf-8")
            if len(rows) % 4 == 0:
                wins = sum(r["candidate_reward"] > r["baseline_reward"] for r in rows)
                print(f"completed {len(rows)}/{len(tasks)} wins {wins}", flush=True)
    wins = sum(r["candidate_reward"] > r["baseline_reward"] for r in rows)
    losses = sum(r["candidate_reward"] < r["baseline_reward"] for r in rows)
    print(json.dumps({"wins": wins, "losses": losses, "ties": len(rows)-wins-losses,
                      "errors": sum(r["candidate_status"] != "DONE" or r["baseline_status"] != "DONE" for r in rows)}))
