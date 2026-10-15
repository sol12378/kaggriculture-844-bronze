"""Summarize route performance by shop and publicly observable rival assets."""
import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "ENV_TRAIN_26330001_16.json").read_text(encoding="utf-8"))
groups = defaultdict(list)
for r in data["rows"]:
    f = r["context"]
    sheep = f["rival_animals"].get("SHEEP", 0)
    cohort = "3plus_sheep" if sheep >= 3 else "under3_sheep"
    for key in (("shop", f["shop"]), ("shop_cohort", f["shop"], cohort),
                ("opponent", r["opponent"]), ("cohort", cohort)):
        groups[(key, r["route"])].append(r)

report = {}
for (key, route), rows in groups.items():
    label = "|".join(key)
    report.setdefault(label, {})[route] = {
        "games": len(rows), "wins": sum(r["halfwin"] for r in rows),
        "mean_margin": round(sum(r["margin"] for r in rows) / len(rows))}

for label in sorted(report):
    print(label)
    for route, result in sorted(report[label].items(), key=lambda x: x[1]["wins"], reverse=True):
        print("  ", route, result)
(HERE / "ENV_TRAIN_SUMMARY.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
