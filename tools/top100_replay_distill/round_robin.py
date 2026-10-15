"""Seat-balanced live-agent league on a held-out seed family.

All agents receive only their own observations. Results are checkpointed after
each pair so a long all-candidate tournament can be resumed exactly.
"""
import argparse
import json
import multiprocessing as mp
import runpy
import sys
from itertools import combinations
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim"))
from fast_eval import run_adaptive

EXISTING = {
    "submitted": ROOT / "top20_counter_20260930" / "main.py",
    "v4": ROOT / "submission_ready_20260930" / "main.py",
    "ready2500": ROOT / "ready_2500_final_20260930" / "main.py",
    "second_meta": ROOT / "second_meta_agent_20260930" / "main.py",
}


def candidates(roster):
    if roster == "all":
        names = sorted(p.name for p in (HERE / "candidates").iterdir()
                       if p.is_dir() and (p / "main.py").is_file())
        paths = {name: HERE / "candidates" / name / "main.py" for name in names}
        return {**EXISTING, **paths}
    paths = {}
    for name in roster.split(","):
        name = name.strip()
        paths[name] = EXISTING.get(name, HERE / "candidates" / name / "main.py")
    return paths


def summary(rows, paths):
    names = list(paths)
    by_name = {n: {"games": 0, "wins": 0, "ties": 0, "margin": 0} for n in names}
    matrix = {n: {} for n in names}
    for key, games in rows.items():
        a, b = key.split("|")
        awins = sum(g["margin_a"] > 0 for g in games)
        bwins = sum(g["margin_a"] < 0 for g in games)
        ties = len(games) - awins - bwins
        matrix[a][b] = {"wins": awins, "losses": bwins, "ties": ties,
                        "mean_margin": round(sum(g["margin_a"] for g in games) / len(games), 2)}
        matrix[b][a] = {"wins": bwins, "losses": awins, "ties": ties,
                        "mean_margin": -matrix[a][b]["mean_margin"]}
        for n, wins, margin in ((a, awins, 1), (b, bwins, -1)):
            by_name[n]["games"] += len(games)
            by_name[n]["wins"] += wins
            by_name[n]["ties"] += ties
            by_name[n]["margin"] += margin * sum(g["margin_a"] for g in games)
    for n, value in by_name.items():
        played = value["games"]
        value["halfwin_rate"] = round((value["wins"] + .5 * value["ties"]) / played, 4) if played else None
        value["mean_margin"] = round(value.pop("margin") / played, 2) if played else None
        value["pair_wins"] = sum(r["wins"] > r["losses"] for r in matrix[n].values())
        value["pair_losses"] = sum(r["wins"] < r["losses"] for r in matrix[n].values())
    ranking = sorted(names, key=lambda n: (by_name[n]["halfwin_rate"] or 0,
                                           by_name[n]["pair_wins"], by_name[n]["mean_margin"] or 0), reverse=True)
    return by_name, matrix, ranking


def pair_task(task):
    a, b, path_a, path_b, seeds = task
    first = run_adaptive(lambda p=path_a: runpy.run_path(str(p))["agent"],
                         lambda p=path_b: runpy.run_path(str(p))["agent"], seeds)
    second = run_adaptive(lambda p=path_b: runpy.run_path(str(p))["agent"],
                          lambda p=path_a: runpy.run_path(str(p))["agent"], seeds)
    games = [{"seed": g["seed"], "seat_a": 0, "margin_a": g["money_0"] - g["money_1"]}
             for g in first]
    games += [{"seed": g["seed"], "seat_a": 1, "margin_a": g["money_1"] - g["money_0"]}
              for g in second]
    return a, b, games


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--roster", default="all")
    parser.add_argument("--start", type=int, default=30330001)
    parser.add_argument("--count", type=int, default=8)
    parser.add_argument("--label", default="FINAL_ALL")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    paths = candidates(args.roster)
    assert all(p.is_file() for p in paths.values())
    seeds = [args.start + 61 * i for i in range(args.count)]
    target = HERE / f"{args.label}_{args.start}_{args.count}.json"
    if target.exists():
        data = json.loads(target.read_text(encoding="utf-8"))
        assert data["seeds"] == seeds and data["roster"] == list(paths)
    else:
        data = {"engine": "FAST_SIM_1327_READY; live agents; both seats", "seeds": seeds,
                "roster": list(paths), "paths": {n: str(p) for n, p in paths.items()}, "pairs": {}}
    tasks = [(a, b, paths[a], paths[b], seeds) for a, b in combinations(paths, 2)
             if f"{a}|{b}" not in data["pairs"]]
    if args.workers > 1:
        pool = mp.Pool(args.workers, maxtasksperchild=10)
        iterator = pool.imap_unordered(pair_task, tasks)
    else:
        pool = None
        iterator = map(pair_task, tasks)
    for index, (a, b, games) in enumerate(iterator, 1):
        key = f"{a}|{b}"
        data["pairs"][key] = games
        if index % max(1, args.workers) == 0 or index == len(tasks):
            data["aggregate"], data["matrix"], data["ranking"] = summary(data["pairs"], paths)
            target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"{len(data['pairs'])}/{len(paths)*(len(paths)-1)//2} pairs; current #1 {data['ranking'][0]}", flush=True)
    if pool:
        pool.close()
        pool.join()


if __name__ == "__main__": main()
