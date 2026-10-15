"""Add one new challenger to the frozen official finalist seed schedule."""
import json
import multiprocessing as mp
from pathlib import Path

from official_validate import one
from round_robin import candidates

HERE = Path(__file__).resolve().parent
CHALLENGER = "rank95_front97"
OPPONENTS = ("rank95_basic", "environment_meta_v2_front97", "environment_meta_front_97",
             "rank32_plus8_front97", "rank32_plus8", "rank88_c_full",
             "rank97_plus4", "submitted", "second_meta")
SEEDS = [36330001 + 67*i for i in range(24)]
PATHS = candidates(",".join((CHALLENGER,) + OPPONENTS))
OUT = HERE / "OFFICIAL_RANK95_FRONT_CHALLENGER_36330001_24.json"


def task_one(task):
    opponent, seat, seed = task
    row = one((PATHS[CHALLENGER], PATHS[opponent], seat, seed))
    row["opponent"] = opponent
    return row


def main():
    if OUT.exists():
        data = json.loads(OUT.read_text(encoding="utf-8"))
        assert data["seeds"] == SEEDS
    else:
        data = {"engine": "official kaggle_environments 1.32.7 path loader; both seats",
                "candidate": CHALLENGER, "seeds": SEEDS, "opponents": OPPONENTS,
                "rows": []}
    seen = {(r["opponent"], r["seed"], r["seat"]) for r in data["rows"]}
    tasks = [(name, seat, seed) for name in OPPONENTS for seed in SEEDS for seat in (0,1)
             if (name, seed, seat) not in seen]
    print("remaining", len(tasks), flush=True)
    with mp.Pool(8, maxtasksperchild=1) as pool:
        for n, result in enumerate(pool.imap_unordered(task_one, tasks), 1):
            data["rows"].append(result)
            if n % 8 == 0 or n == len(tasks):
                OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
                if n % 48 == 0 or n == len(tasks):
                    print(f"completed {n}/{len(tasks)}; errors "
                          f"{sum(r['candidate_status']!='DONE' or r['baseline_status']!='DONE' for r in data['rows'])}", flush=True)
    for name in OPPONENTS:
        rows = [r for r in data["rows"] if r["opponent"] == name]
        margins = [r["candidate_reward"] - r["baseline_reward"] for r in rows]
        print(name, sum(m>0 for m in margins), sum(m<0 for m in margins),
              sum(m==0 for m in margins), round(sum(margins)/len(margins),2))


if __name__ == "__main__": main()
