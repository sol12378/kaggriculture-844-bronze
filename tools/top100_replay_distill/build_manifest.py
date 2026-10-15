"""Freeze episode selection and a globally disjoint validation partition."""

import json
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGETS = json.loads((HERE / "TARGETS.json").read_text(encoding="utf-8"))["rows"]
by_episode = defaultdict(lambda: {"source_ranks": [], "agents": []})
per_rank = {}
for target in TARGETS:
    rank = target["rank"]
    path = HERE / "episode_lists" / f"rank{rank:03d}_submission{target['submission_id']}.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert len(data["selected_ids"]) == 8, (rank, len(data["selected_ids"]))
    per_rank[str(rank)] = {"team_id": target["team_id"], "team_name": target["team_name"],
                           "submission_id": target["submission_id"], "episode_ids": data["selected_ids"]}
    for episode in data["selected"]:
        key = str(episode["id"])
        by_episode[key]["source_ranks"].append(rank)
        by_episode[key]["agents"] = episode["agents"]
        by_episode[key]["end_time"] = episode.get("endTime")

# Most recent 3 matches per team are validation. If a match was selected by
# another team as development, the whole match remains validation.
holdout = {eid for rank in per_rank.values() for eid in rank["episode_ids"][:3]}
for eid, row in by_episode.items():
    row["split"] = "validation" if eid in holdout else "development"
for rank in per_rank.values():
    rank["development_ids"] = [eid for eid in rank["episode_ids"] if eid not in holdout]
    rank["validation_ids"] = [eid for eid in rank["episode_ids"] if eid in holdout]

result = {"schema": "top100-public-episodes/v1",
          "rule": "8 newest completed public episodes per frozen top-100 leaderboard submission; newest 3 per team globally reserved for validation",
          "target_count": len(TARGETS), "selection_count": sum(len(r["episode_ids"]) for r in per_rank.values()),
          "unique_episodes": len(by_episode), "development_episodes": sum(r["split"] == "development" for r in by_episode.values()),
          "validation_episodes": len(holdout), "ranks": per_rank, "episodes": dict(by_episode)}
(HERE / "MANIFEST.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print({k: result[k] for k in ("target_count", "selection_count", "unique_episodes", "development_episodes", "validation_episodes")})
