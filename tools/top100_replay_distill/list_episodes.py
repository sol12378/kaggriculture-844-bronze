"""Persist public episode metadata for each frozen top-100 team."""

import json
import time
from datetime import datetime, timezone
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

HERE = Path(__file__).resolve().parent
TARGETS = json.loads((HERE / "TARGETS.json").read_text(encoding="utf-8"))["rows"]
EPISODES = HERE / "episode_lists"
EPISODES.mkdir(exist_ok=True)
api = KaggleApi()
api.authenticate()


def episode_id(e):
    return str(e.get("id", ""))


for row in TARGETS:
    rank = row["rank"]
    sid = row["submission_id"]
    path = EPISODES / f"rank{rank:03d}_submission{sid}.json"
    if path.exists():
        continue
    for attempt in range(10):
        try:
            records = [e.to_dict() for e in api.competition_list_episodes(sid)]
            eligible = [e for e in records if str(e.get("state")) in ("EpisodeState.COMPLETED", "COMPLETED")
                        and str(e.get("type")) in ("EpisodeType.EPISODE_TYPE_PUBLIC", "EPISODE_TYPE_PUBLIC")]
            # The API delivers newest episodes first. Keep its order and the full metadata.
            selected = eligible[:8]
            result = {"rank": rank, "team_id": row["team_id"], "team_name": row["team_name"],
                      "submission_id": sid, "retrieved_utc": datetime.now(timezone.utc).isoformat(),
                      "total_episodes": len(records), "eligible_public_completed": len(eligible),
                      "selected_ids": [episode_id(e) for e in selected],
                      "development_ids": [episode_id(e) for e in selected[3:]],
                      "validation_ids": [episode_id(e) for e in selected[:3]],
                      "selected": selected}
            path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"rank {rank:03d}: {len(selected)} episodes ({len(eligible)} eligible)", flush=True)
            time.sleep(1.2)
            break
        except Exception as exc:
            if "429" in str(exc):
                wait = min(10 * (attempt + 1), 60)
                print(f"rate limited rank {rank}; wait {wait}s", flush=True)
                time.sleep(wait)
            else:
                print(f"rank {rank} error {exc}", flush=True)
                time.sleep(2)
    else:
        print(f"FAILED rank {rank}", flush=True)

done = list(EPISODES.glob("rank*_submission*.json"))
print(json.dumps({"target_teams": len(TARGETS), "listed": len(done)}), flush=True)
