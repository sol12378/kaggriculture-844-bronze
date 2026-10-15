"""Resume team-submission reads with conservative rate-limit backoff."""
import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

HERE = Path(__file__).resolve().parent
path = HERE / "TARGETS.json"
data = json.loads(path.read_text(encoding="utf-8"))
api = KaggleApi()
api.authenticate()

def save():
    data["finished_utc"] = datetime.now(timezone.utc).isoformat()
    data["complete"] = sum("submission_id" in r for r in data["rows"])
    data["score_matches_snapshot"] = sum(r.get("score_matches_snapshot", False) for r in data["rows"])
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    with (HERE / "TARGETS.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["rank", "team_id", "team_name", "leaderboard_score",
                  "submission_id", "submission_score", "score_matches_snapshot"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: r.get(k) for k in fields} for r in data["rows"])

for row in data["rows"]:
    if "submission_id" in row:
        continue
    for attempt in range(8):
        try:
            submissions = [s.to_dict() for s in api.competition_team_submissions(row["team_id"])]
            if not submissions:
                raise RuntimeError("no tracked submissions")
            target = min(submissions, key=lambda s: (abs(float(s["publicScore"]) - row["leaderboard_score"]),
                                                      -float(s["publicScore"])))
            if abs(float(target["publicScore"]) - row["leaderboard_score"]) > 0.11:
                target = max(submissions, key=lambda s: float(s["publicScore"]))
            row.update(submission_id=target["id"], submission_score=float(target["publicScore"]),
                       score_matches_snapshot=abs(float(target["publicScore"]) - row["leaderboard_score"]) <= 0.11,
                       tracked_submissions=submissions)
            row.pop("error", None)
            save()
            print(f"rank {row['rank']} complete; total {data['complete']}/100", flush=True)
            time.sleep(1.0)
            break
        except Exception as exc:
            row["error"] = str(exc)
            save()
            if "429" in str(exc):
                wait = min(10 * (attempt + 1), 60)
                print(f"rate limit at rank {row['rank']}; wait {wait}s", flush=True)
                time.sleep(wait)
            else:
                print(f"rank {row['rank']} error: {exc}", flush=True)
                time.sleep(2)
print(json.dumps({"complete": data["complete"], "matched": data["score_matches_snapshot"]}))
