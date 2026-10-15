"""Download all current public hosted replays for read-only diagnosis."""
import json
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

HERE = Path(__file__).resolve().parent
OUT = HERE / "replays"
OUT.mkdir(exist_ok=True)
EPISODES = [r["episode_id"] for r in json.loads((HERE / "HOSTED_EPISODES.json").read_text(encoding="utf-8"))
            if r["type"] == "EPISODE_TYPE_PUBLIC" and r["outcome"]]
api = KaggleApi()
api.authenticate()
for episode_id in EPISODES:
    target = OUT / f"episode-{episode_id}-replay.json"
    if not target.exists():
        api.competition_episode_replay(episode_id, path=str(OUT), quiet=True)
    data = json.loads(target.read_text(encoding="utf-8"))
    print(json.dumps({"episode_id": episode_id, "seed": data.get("info", {}).get("seed"),
                      "rewards": data.get("rewards"), "teams": data.get("info", {}).get("TeamNames"),
                      "steps": len(data.get("steps", [])), "bytes": target.stat().st_size}, ensure_ascii=True))
