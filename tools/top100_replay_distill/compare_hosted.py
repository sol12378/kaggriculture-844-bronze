"""Compare submitted agent's observed economy to top-100 public trajectories."""

import json
from pathlib import Path
from statistics import median

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
HOSTED = ROOT / "hosted_gap_analysis_20260930" / "replays"
TOP = [json.loads(line) for line in (HERE / "TRAJECTORIES.jsonl").read_text(encoding="utf-8").splitlines()]
STEPS = (47, 119, 239, 479, 695, 718)


def snap(replay, step, seat):
    obs = replay["steps"][step][seat]["observation"]
    farm = obs["farms"][seat]
    tiles = {}
    for line in farm["tiles"]:
        for tile in line:
            if not isinstance(tile, dict):
                continue
            label = f"plant:{tile.get('crop')}" if tile.get("kind") == "PLANT" else f"animal:{tile.get('animal')}"
            tiles[label] = tiles.get(label, 0) + 1
    shed = obs["private"].get("shed", {})
    return {"cash": farm["money"], "hands": len(farm["hands"]),
            "tiles": tiles, "shed_value": sum(q * obs["market"]["prices"].get(item, 0) for item, q in shed.items())}


own = []
for path in sorted(HOSTED.glob("episode-*-replay.json")):
    replay = json.loads(path.read_bytes())
    if "sol12378" not in replay["info"]["TeamNames"]:
        continue
    seat = replay["info"]["TeamNames"].index("sol12378")
    own.append({"episode_id": str(replay["info"]["EpisodeId"]), "win": replay["rewards"][seat] > replay["rewards"][1 - seat],
                "snapshots": {str(s): snap(replay, s, seat) for s in STEPS}})


def metric(rows, step, key):
    if key.startswith("tile:"):
        return median(r["snapshots"][str(step)]["tiles"].get(key[5:], 0) for r in rows)
    if key == "shed_value":
        return median(r["snapshots"][str(step)].get("shed_value", r["snapshots"][str(step)].get("shed_mark_value")) for r in rows)
    return median(r["snapshots"][str(step)][key] for r in rows)


cohorts = {"submitted": own,
           "rank01_20": [r for r in TOP if r["rank"] <= 20],
           "rank21_50": [r for r in TOP if 21 <= r["rank"] <= 50],
           "rank51_100": [r for r in TOP if 51 <= r["rank"] <= 100]}
report = {"schema": "top100-hosted-economy-comparison/v1",
          "note": "Unpaired public games; descriptive only; rank cohort matches may differ in seeds and opponents",
          "groups": {}}
for group, rows in cohorts.items():
    if not rows:
        continue
    report["groups"][group] = {"games": len(rows), "snapshot_medians": {
        str(s): {key: round(metric(rows, s, key), 2)
                 for key in ("cash", "hands", "shed_value", "tile:plant:STRAWBERRY",
                             "tile:plant:WHEAT", "tile:animal:COW", "tile:animal:SHEEP", "tile:animal:GOOSE")}
        for s in STEPS}}
(HERE / "HOSTED_COMPARISON.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(report["groups"], ensure_ascii=False))
