"""Final fair comparison on three untouched official seed families."""
import json
from pathlib import Path
from aggregate_two_families import margins_initial, margins_second, interval

HERE = Path(__file__).resolve().parent
third = json.loads((HERE / "OFFICIAL_THIRD_FAMILY_LEAGUE_40330001_32.json").read_text(encoding="utf-8"))
assert sum(map(len, third["pairs"].values())) == 640
assert third["errors"] == 0
TOP = ("rank95_front97", "rank32_plus8_front97", "environment_meta_front_97")
OPPONENTS = TOP + ("rank88_c_full", "submitted")


def margins_third(a,b):
    key = f"{a}|{b}"
    sign = 1
    if key not in third["pairs"]:
        key = f"{b}|{a}"
        sign = -1
    return {(r["seed"], r["seat_a"] if sign==1 else 1-r["seat_a"]):
            sign*r["margin_a"] for r in third["pairs"][key]}


report = {}
ranking = []
for agent in TOP:
    report[agent] = {}
    for opponent in OPPONENTS:
        if agent == opponent: continue
        a = margins_initial(agent, opponent)
        b = margins_second(agent, opponent)
        c = margins_third(agent, opponent)
        assert len(a)==48 and len(b)==64 and len(c)==64
        assert not (set(a)&set(b) or set(a)&set(c) or set(b)&set(c))
        all_rows = {**a, **b, **c}
        vals = list(all_rows.values())
        report[agent][opponent] = {
            "games": 176, "seeds": 88,
            "wins": sum(v>0 for v in vals), "losses": sum(v<0 for v in vals),
            "ties": sum(v==0 for v in vals),
            "halfwin_rate": round((sum(v>0 for v in vals)+.5*sum(v==0 for v in vals))/176,4),
            "mean_margin": round(sum(vals)/176,2),
            "seed_bootstrap_95_win": interval(all_rows,"win"),
            "seed_bootstrap_95_margin": interval(all_rows,"margin")}
    values = list(report[agent].values())
    peer_values = [v for n,v in report[agent].items() if n != "submitted"]
    ranking.append({"agent": agent,
        "wins": sum(v["wins"] for v in values), "losses": sum(v["losses"] for v in values),
        "ties": sum(v["ties"] for v in values), "games": 704,
        "halfwin_rate": round(sum(v["wins"]+.5*v["ties"] for v in values)/704,4),
        "peer_only_halfwin": round(sum(v["wins"]+.5*v["ties"] for v in peer_values)/(176*3),4),
        "mean_margin": round(sum(v["mean_margin"] for v in values)/4,2),
        "pair_wins": sum(v["wins"]>v["losses"] for v in values),
        "pair_losses": sum(v["wins"]<v["losses"] for v in values),
        "worst_halfwin_rate": min(v["halfwin_rate"] for v in values),
        "direct": report[agent]})
ranking.sort(key=lambda r:(r["halfwin_rate"],r["peer_only_halfwin"],r["pair_wins"],r["mean_margin"]),reverse=True)
out = {"engine": "official kaggle_environments 1.32.7 path loader", "seed_families": [
    [36330001+67*i for i in range(24)], [38330001+67*i for i in range(32)],
    third["seeds"]], "errors": 0, "rankings": ranking, "winner": ranking[0]["agent"]}
(HERE / "THREE_FAMILY_FINAL_SELECTION.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps({"winner": out["winner"], "rankings": [
    {k:v for k,v in r.items() if k!="direct"} for r in ranking]}, indent=2))
