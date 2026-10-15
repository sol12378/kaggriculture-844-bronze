"""Summarize team-balanced strategies and identify reproducible families."""

import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).resolve().parent
rows = [json.loads(line) for line in (HERE / "TRAJECTORIES.jsonl").read_text(encoding="utf-8").splitlines()]
by_rank = defaultdict(list)
for row in rows:
    by_rank[row["rank"]].append(row)


def field(row, snap, key):
    return row["snapshots"][str(snap)][key]


def get_tiles(row, snap):
    return row["snapshots"][str(snap)]["tiles"]


def archetype(row):
    tiles = get_tiles(row, 239)
    cow = tiles.get("animal:COW", 0)
    sheep = tiles.get("animal:SHEEP", 0)
    goose = tiles.get("animal:GOOSE", 0)
    berry = tiles.get("plant:STRAWBERRY", 0)
    melon = tiles.get("plant:MELON", 0)
    wheat = tiles.get("plant:WHEAT", 0)
    if cow >= 10 and berry >= 15:
        return "cow_berry"
    if sheep >= 8 and goose >= 8:
        return "sheep_goose"
    if cow >= 10:
        return "cow_other"
    if berry >= 20 and melon >= 10:
        return "berry_melon"
    if wheat >= 20:
        return "wheat_heavy"
    return "mixed_other"


def opening(row):
    return [[int(o[0]), o[1], o[2] if len(o) > 2 else None, o[3] if len(o) > 3 else None]
            for o in row["opening_orders"] if int(o[0]) < 8 and o[1] != "SELL"]


team_rows = []
for rank, samples in sorted(by_rank.items()):
    feature = {}
    for step in (47, 119, 239, 479, 695, 718):
        feature[str(step)] = {"cash": round(median(field(r, step, "cash") for r in samples), 1),
                              "hands": median(field(r, step, "hands") for r in samples),
                              "shed_value": round(median(field(r, step, "shed_mark_value") for r in samples), 1),
                              "tiles": {k: round(median(get_tiles(r, step).get(k, 0) for r in samples), 1)
                                        for k in sorted({item for r in samples for item in get_tiles(r, step)})}}
    types = Counter(archetype(r) for r in samples)
    opening_signatures = Counter(json.dumps(opening(r), separators=(",", ":")) for r in samples)
    team_rows.append({"rank": rank, "team": samples[0]["team_name"], "episodes": len(samples),
                      "dev_episodes": sum(r["split"] == "development" for r in samples),
                      "val_episodes": sum(r["split"] == "validation" for r in samples),
                      "wins_in_selected": sum(r["reward"] > r["opponent_reward"] for r in samples),
                      "archetypes": dict(types), "top_opening": json.loads(opening_signatures.most_common(1)[0][0]),
                      "opening_repeat": opening_signatures.most_common(1)[0][1],
                      "snapshots": feature})

cohorts = {}
for label, lo, hi in (("rank01_20", 1, 20), ("rank21_50", 21, 50), ("rank51_100", 51, 100)):
    teams = [t for t in team_rows if lo <= t["rank"] <= hi]
    types = Counter()
    for t in teams:
        types.update(t["archetypes"])
    medians = {}
    for step in (47, 119, 239, 479, 695, 718):
        medians[str(step)] = {metric: round(median(t["snapshots"][str(step)][metric] for t in teams), 1)
                              for metric in ("cash", "hands", "shed_value")}
    cohorts[label] = {"teams": len(teams), "trajectories": sum(t["episodes"] for t in teams),
                      "archetype_episodes": dict(types), "team_median_metrics": medians}

result = {"schema": "top100-distilled-patterns/v1", "caveat": "8 recent public matches per team; win rate is selection biased; orders are submitted quantities, not confirmed fills",
          "teams_covered": len(team_rows), "trajectories": len(rows), "cohorts": cohorts, "team_rows": team_rows}
(HERE / "PATTERNS.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"teams_covered": len(team_rows), "trajectories": len(rows), "cohorts": cohorts}, ensure_ascii=False))
