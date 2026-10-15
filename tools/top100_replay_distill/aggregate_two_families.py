"""Combine two untouched official seed families with seat-paired uncertainty."""
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent
first = json.loads((HERE / "OFFICIAL_FINAL_LEAGUE_36330001_24.json").read_text(encoding="utf-8"))
challenge = json.loads((HERE / "OFFICIAL_RANK95_FRONT_CHALLENGER_36330001_24.json").read_text(encoding="utf-8"))
second_files = {
    "rank95_front97": json.loads((HERE / "OFFICIAL_CONFIRM_rank95_front97_38330001_32.json").read_text(encoding="utf-8")),
    "rank32_plus8_front97": json.loads((HERE / "OFFICIAL_CONFIRM_rank32_plus8_front97_38330001_32.json").read_text(encoding="utf-8")),
    "environment_meta_front_97": json.loads((HERE / "OFFICIAL_CONFIRM_environment_meta_front_97_38330001_32.json").read_text(encoding="utf-8")),
}
triangle = json.loads((HERE / "OFFICIAL_CONFIRM_TRIANGLE_38330001_32.json").read_text(encoding="utf-8"))
TOP = ("rank95_front97", "rank32_plus8_front97", "environment_meta_front_97")
OTHERS = ("rank88_c_full", "rank97_plus4", "submitted", "second_meta")


def margins_initial(a, b):
    if a == "rank95_front97" or b == "rank95_front97":
        other = b if a == "rank95_front97" else a
        sign = 1 if a == "rank95_front97" else -1
        rows = [r for r in challenge["rows"] if r["opponent"] == other]
        return {(r["seed"], r["seat"] if sign == 1 else 1-r["seat"]):
                sign * (r["candidate_reward"]-r["baseline_reward"]) for r in rows}
    key = f"{a}|{b}"
    sign = 1
    if key not in first["pairs"]:
        key = f"{b}|{a}"
        sign = -1
    return {(r["seed"], r["seat_a"] if sign == 1 else 1-r["seat_a"]):
            sign * r["margin_a"] for r in first["pairs"][key]}


def margins_second(a, b):
    # Direct confirmation has precedence; the remaining top pair is in triangle.
    if a == "rank95_front97" or b == "rank95_front97":
        other = b if a == "rank95_front97" else a
        sign = 1 if a == "rank95_front97" else -1
        rows = [r for r in second_files["rank95_front97"]["rows"] if r["opponent"] == other]
        return {(r["seed"], r["seat"] if sign == 1 else 1-r["seat"]):
                sign * (r["candidate_reward"]-r["baseline_reward"]) for r in rows}
    if {a,b} == {"rank32_plus8_front97", "environment_meta_front_97"}:
        key = f"environment_meta_front_97|rank32_plus8_front97"
        sign = 1 if a == "environment_meta_front_97" else -1
        return {(r["seed"], r["seat_a"] if sign == 1 else 1-r["seat_a"]):
                sign * r["margin_a"] for r in triangle["pairs"][key]}
    if a in ("rank32_plus8_front97", "environment_meta_front_97") and b == "submitted":
        key = f"{a}|submitted"
        return {(r["seed"], r["seat_a"]): r["margin_a"] for r in triangle["pairs"][key]}
    if a in TOP and b in OTHERS:
        rows = [r for r in second_files[a]["rows"] if r["opponent"] == b]
        return {(r["seed"], r["seat"]): r["candidate_reward"]-r["baseline_reward"] for r in rows}
    raise KeyError((a,b))


def interval(pairs, kind):
    values = []
    for seed in sorted({s for s,_ in pairs}):
        one, two = pairs[(seed,0)], pairs[(seed,1)]
        if kind == "win":
            values.append((int(one>0)+int(two>0)+.5*int(one==0)+.5*int(two==0))/2)
        else:
            values.append((one+two)/2)
    rng = random.Random(20261001)
    means = sorted(sum(rng.choice(values) for _ in values)/len(values) for _ in range(5000))
    return [round(means[125], 4 if kind=="win" else 2),
            round(means[4874], 4 if kind=="win" else 2)]


report = {}
for agent in TOP:
    report[agent] = {}
    for opponent in TOP + OTHERS:
        if agent == opponent: continue
        a = margins_initial(agent, opponent)
        b = margins_second(agent, opponent)
        assert len(a) == 48 and len(b) == 64 and not (set(a) & set(b)), (agent, opponent, len(a), len(b))
        all_rows = {**a, **b}
        values = list(all_rows.values())
        report[agent][opponent] = {
            "games": len(values), "seeds": len({s for s,_ in all_rows}),
            "wins": sum(v>0 for v in values), "losses": sum(v<0 for v in values),
            "ties": sum(v==0 for v in values),
            "halfwin_rate": round((sum(v>0 for v in values)+.5*sum(v==0 for v in values))/len(values),4),
            "mean_margin": round(sum(values)/len(values),2),
            "seed_bootstrap_95_win": interval(all_rows,"win"),
            "seed_bootstrap_95_margin": interval(all_rows,"margin")}

ranking = []
for agent in TOP:
    vals = list(report[agent].values())
    ranking.append({"agent": agent,
                    "wins": sum(v["wins"] for v in vals), "losses": sum(v["losses"] for v in vals),
                    "ties": sum(v["ties"] for v in vals), "games": sum(v["games"] for v in vals),
                    "halfwin_rate": round(sum(v["wins"]+.5*v["ties"] for v in vals)/sum(v["games"] for v in vals),4),
                    "mean_margin": round(sum(v["mean_margin"] for v in vals)/len(vals),2),
                    "pair_wins": sum(v["wins"]>v["losses"] for v in vals),
                    "pair_losses": sum(v["wins"]<v["losses"] for v in vals),
                    "direct": report[agent]})
ranking.sort(key=lambda r: (r["halfwin_rate"], r["pair_wins"], r["mean_margin"]), reverse=True)
out = {"engine": "official kaggle_environments 1.32.7 path loader", "seed_families": [first["seeds"], second_files["rank95_front97"]["seeds"]],
       "errors": 0, "ranking": ranking, "winner": ranking[0]["agent"]}
(HERE / "TWO_FAMILY_FINAL_SELECTION.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps({"winner": out["winner"], "ranking": [{k:v for k,v in r.items() if k != "direct"} for r in ranking]}, indent=2))
