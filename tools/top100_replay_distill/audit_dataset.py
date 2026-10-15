"""Check top-100 provenance, split isolation and compressed replay hashes."""

import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
targets = json.loads((HERE / "TARGETS.json").read_text(encoding="utf-8"))
manifest = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
audits = [json.loads(line) for line in (HERE / "REPLAY_AUDIT.jsonl").read_text(encoding="utf-8").splitlines()]
trajectories = [json.loads(line) for line in (HERE / "TRAJECTORIES.jsonl").read_text(encoding="utf-8").splitlines()]
assert len(targets["rows"]) == 100
assert sorted(r["rank"] for r in targets["rows"]) == list(range(1,101))
assert len(manifest["episodes"]) == 645
assert manifest["selection_count"] == 800
assert len(audits) == 645 == len({a["episode_id"] for a in audits})
assert len(trajectories) == 800 == len({(r["episode_id"],r["rank"]) for r in trajectories})
assert all(r["split"] == manifest["episodes"][r["episode_id"]]["split"] for r in trajectories)
assert set(e for r in manifest["ranks"].values() for e in r["development_ids"]).isdisjoint(
    set(e for r in manifest["ranks"].values() for e in r["validation_ids"]))
for i, record in enumerate(audits,1):
    eid = record["episode_id"]
    path = HERE / "replays" / f"episode-{eid}-replay.json.gz"
    assert path.is_file()
    with gzip.open(path,"rb") as handle:
        raw = handle.read()
    assert len(raw) == record["raw_bytes"]
    assert hashlib.sha256(raw).hexdigest() == record["sha256"]
    if i % 100 == 0:
        print(f"hashes {i}/645 verified",flush=True)
result = {"schema":"top100-dataset-audit/v1", "targets":100,
          "score_matches_at_fetch":sum(r["score_matches_snapshot"] for r in targets["rows"]),
          "selection_count":800,"unique_replays":645,"hash_verified":645,
          "development_unique":manifest["development_episodes"],
          "validation_unique":manifest["validation_episodes"],
          "development_trajectories":sum(r["split"]=="development" for r in trajectories),
          "validation_trajectories":sum(r["split"]=="validation" for r in trajectories),
          "leakage":False}
(HERE / "DATA_AUDIT.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result))
