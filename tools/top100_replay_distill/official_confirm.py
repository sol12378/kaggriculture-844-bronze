"""Independent-seed official confirmation of the provisional champion."""
import argparse
import json
import multiprocessing as mp
from pathlib import Path

from official_validate import one
from round_robin import candidates

HERE = Path(__file__).resolve().parent


def task_one(task):
    name, path_me, path_other, seat, seed = task
    row = one((path_me, path_other, seat, seed))
    row["opponent"] = name
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate")
    parser.add_argument("--opponents", required=True)
    parser.add_argument("--start", type=int, default=38330001)
    parser.add_argument("--count", type=int, default=32)
    parser.add_argument("--workers", type=int, default=8)
    args = parser.parse_args()
    names = [n.strip() for n in args.opponents.split(",")]
    assert args.candidate not in names
    paths = candidates(",".join([args.candidate] + names))
    seeds = [args.start + 67*i for i in range(args.count)]
    target = HERE / f"OFFICIAL_CONFIRM_{args.candidate}_{args.start}_{args.count}.json"
    if target.exists():
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["seeds"] == seeds and data["opponents"] == names
    else:
        data = {"engine": "official kaggle_environments 1.32.7 path loader; both seats",
                "candidate": args.candidate, "seeds": seeds, "opponents": names, "rows": []}
    seen = {(r["opponent"], r["seed"], r["seat"]) for r in data["rows"]}
    tasks = [(name, paths[args.candidate], paths[name], seat, seed)
             for name in names for seed in seeds for seat in (0, 1)
             if (name, seed, seat) not in seen]
    print("remaining", len(tasks), flush=True)
    if tasks:
        with mp.Pool(args.workers, maxtasksperchild=1) as pool:
            for n, result in enumerate(pool.imap_unordered(task_one, tasks), 1):
                data["rows"].append(result)
                if n % 8 == 0 or n == len(tasks):
                    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
                    if n % 64 == 0 or n == len(tasks):
                        print(f"completed {n}/{len(tasks)}; errors "
                              f"{sum(r['candidate_status']!='DONE' or r['baseline_status']!='DONE' for r in data['rows'])}", flush=True)
    result = {}
    for name in names:
        rows = [r for r in data["rows"] if r["opponent"] == name]
        margins = [r["candidate_reward"] - r["baseline_reward"] for r in rows]
        result[name] = {"games": len(rows), "wins": sum(m>0 for m in margins),
                        "losses": sum(m<0 for m in margins), "ties": sum(m==0 for m in margins),
                        "mean_margin": round(sum(margins)/len(margins),2)}
    data["summary"] = result
    target.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__": main()
