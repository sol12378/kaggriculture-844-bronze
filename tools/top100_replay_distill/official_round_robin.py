"""Final all-pairs tournament with Kaggle's path-loaded engine 1.32.7."""
import argparse
import json
import multiprocessing as mp
from itertools import combinations
from pathlib import Path

from official_validate import one
from round_robin import candidates, summary

HERE = Path(__file__).resolve().parent


def match(task):
    a, b, pa, pb, seat, seed = task
    result = one((pa, pb, seat, seed))
    result["a"] = a
    result["b"] = b
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roster", required=True)
    parser.add_argument("--start", type=int, default=36330001)
    parser.add_argument("--count", type=int, default=24)
    parser.add_argument("--label", default="OFFICIAL_FINAL_LEAGUE")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    paths = candidates(args.roster)
    assert all(p.is_file() for p in paths.values())
    seeds = [args.start + 67 * i for i in range(args.count)]
    target = HERE / f"{args.label}_{args.start}_{args.count}.json"
    if target.exists():
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["seeds"] == seeds and data["roster"] == list(paths)
    else:
        data = {"engine": "official kaggle_environments 1.32.7 path loader; both seats",
                "seeds": seeds, "roster": list(paths),
                "paths": {n: str(p) for n,p in paths.items()}, "pairs": {}}
    tasks = []
    for a, b in combinations(paths, 2):
        key = f"{a}|{b}"
        seen = {(r["seed"], r["seat_a"]) for r in data["pairs"].get(key, [])}
        for seed in seeds:
            for seat in (0, 1):
                if (seed, seat) not in seen: tasks.append((a, b, paths[a], paths[b], seat, seed))
    print("remaining", len(tasks), "of", len(paths)*(len(paths)-1)//2 * 2 * len(seeds), flush=True)
    if tasks:
        with mp.Pool(args.workers, maxtasksperchild=1) as pool:
            for n, result in enumerate(pool.imap_unordered(match, tasks), 1):
                a, b = result.pop("a"), result.pop("b")
                key = f"{a}|{b}"
                margin = (result["candidate_reward"] - result["baseline_reward"]
                          if result["candidate_reward"] is not None and result["baseline_reward"] is not None
                          else None)
                result["seat_a"] = result.pop("seat")
                result["margin_a"] = margin
                data["pairs"].setdefault(key, []).append(result)
                if n % 4 == 0 or n == len(tasks):
                    valid = {key: kept for key,rows in data["pairs"].items()
                             if (kept := [r for r in rows if r["margin_a"] is not None])}
                    data["aggregate"], data["matrix"], data["ranking"] = summary(valid, paths)
                    data["errors"] = sum(r["candidate_status"] != "DONE" or r["baseline_status"] != "DONE"
                                         for rows in data["pairs"].values() for r in rows)
                    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
                    if n % 24 == 0 or n == len(tasks):
                        print(f"completed {n}/{len(tasks)}; current #1 {data['ranking'][0]}; errors {data['errors']}", flush=True)
    print(json.dumps({"ranking": data.get("ranking"), "aggregate": data.get("aggregate"),
                      "errors": data.get("errors")}, indent=2))


if __name__ == "__main__": main()
