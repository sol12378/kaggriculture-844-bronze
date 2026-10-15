"""Read-only hosted episode inventory for the latest Kaggriculture submission."""
from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

SUBMISSION = 56702533
HERE = Path(__file__).resolve().parent
api = KaggleApi()
api.authenticate()
episodes = [e.to_dict() for e in api.competition_list_episodes(SUBMISSION)]
rows = []
for episode in episodes:
    agents = episode.get("agents") or []
    ours = next((a for a in agents if a.get("submissionId") == SUBMISSION), None)
    other = next((a for a in agents if a.get("submissionId") != SUBMISSION), None)
    if ours is None or other is None:
        continue
    own_reward = ours.get("reward")
    other_reward = other.get("reward")
    outcome = None
    if own_reward is not None and other_reward is not None:
        outcome = "win" if own_reward > other_reward else "loss" if own_reward < other_reward else "tie"
    rows.append({
        "episode_id": episode["id"],
        "type": episode.get("type"),
        "state": episode.get("state"),
        "end_time": episode.get("endTime"),
        "seat": ours.get("index", 0),
        "opponent": other.get("teamName"),
        "opponent_submission_id": other.get("submissionId"),
        "own_reward": own_reward,
        "opponent_reward": other_reward,
        "margin": own_reward - other_reward if outcome else None,
        "outcome": outcome,
    })
rows.sort(key=lambda r: r["episode_id"])
public = [r for r in rows if r["type"] == "EPISODE_TYPE_PUBLIC" and r["outcome"]]
groups = defaultdict(list)
for r in public:
    groups[(r["opponent"], r["opponent_submission_id"])].append(r)
summary = {
    "submission_id": SUBMISSION,
    "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    "public_completed": len(public),
    "outcomes": dict(Counter(r["outcome"] for r in public)),
    "by_seat": {str(s): dict(Counter(r["outcome"] for r in public if r["seat"] == s)) for s in (0, 1)},
    "opponents": [
        {"name": name, "submission_id": sid, "games": len(v),
         "outcomes": dict(Counter(r["outcome"] for r in v)),
         "mean_margin": sum(r["margin"] for r in v) / len(v)}
        for (name, sid), v in sorted(groups.items(), key=lambda kv: kv[0][0] or "")
    ],
    "losses": [r for r in public if r["outcome"] == "loss"],
}
(HERE / "HOSTED_EPISODES.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
(HERE / "HOSTED_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in summary.items() if k != "opponents"}, ensure_ascii=False, indent=2))
