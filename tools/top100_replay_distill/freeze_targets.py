"""Freeze the current public top-100 teams and each team's best tracked agent."""
import csv
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

HERE = Path(__file__).resolve().parent
api = KaggleApi()
api.authenticate()
started = datetime.now(timezone.utc).isoformat()
leaders = [s.to_dict() for s in api.competition_leaderboard_view("kaggriculture", page_size=100)]
assert len(leaders) == 100

def fetch(index, leader):
    error = None
    for attempt in range(3):
        try:
            submissions = [s.to_dict() for s in api.competition_team_submissions(leader["teamId"])]
            if not submissions:
                raise RuntimeError("no tracked submissions")
            target = min(submissions, key=lambda s: (abs(float(s["publicScore"]) - float(leader["score"])),
                                                      -float(s["publicScore"])))
            if abs(float(target["publicScore"]) - float(leader["score"])) > 0.11:
                target = max(submissions, key=lambda s: float(s["publicScore"]))
            return {"rank": index + 1, "team_id": leader["teamId"],
                    "team_name": leader["teamName"], "leaderboard_score": float(leader["score"]),
                    "submission_id": target["id"], "submission_score": float(target["publicScore"]),
                    "score_matches_snapshot": abs(float(target["publicScore"]) - float(leader["score"])) <= 0.11,
                    "tracked_submissions": submissions}
        except Exception as exc:
            error = str(exc)
            time.sleep(0.5 * (attempt + 1))
    return {"rank": index + 1, "team_id": leader["teamId"], "team_name": leader["teamName"],
            "leaderboard_score": float(leader["score"]), "error": error}

rows = []
with ThreadPoolExecutor(max_workers=4) as pool:
    futures = [pool.submit(fetch, i, leader) for i, leader in enumerate(leaders)]
    for completed, future in enumerate(as_completed(futures), 1):
        rows.append(future.result())
        if completed % 20 == 0:
            print(f"teams {completed}/100", flush=True)
rows.sort(key=lambda r: r["rank"])
result = {"schema": "top100-targets/v1", "started_utc": started,
          "finished_utc": datetime.now(timezone.utc).isoformat(), "rows": rows,
          "complete": sum("submission_id" in r for r in rows),
          "score_matches_snapshot": sum(r.get("score_matches_snapshot", False) for r in rows)}
(HERE / "TARGETS.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
with (HERE / "TARGETS.csv").open("w", encoding="utf-8-sig", newline="") as handle:
    writer = csv.DictWriter(handle, fieldnames=["rank", "team_id", "team_name", "leaderboard_score",
                                                "submission_id", "submission_score", "score_matches_snapshot"])
    writer.writeheader()
    writer.writerows({k: r.get(k) for k in writer.fieldnames} for r in rows)
print(json.dumps({k: result[k] for k in ("started_utc", "finished_utc", "complete", "score_matches_snapshot")}, indent=2))
