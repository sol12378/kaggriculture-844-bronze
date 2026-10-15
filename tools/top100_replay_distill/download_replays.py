"""Download, verify and compress unique public replays; safe to resume."""

import gzip
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

from kaggle.api.kaggle_api_extended import KaggleApi

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
MANIFEST = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
DEST = HERE / "replays"
DEST.mkdir(exist_ok=True)
OLD = ROOT / "top20_replay_distill_20260930" / "replays"
AUDIT = HERE / "REPLAY_AUDIT.jsonl"
api = KaggleApi()
api.authenticate()


def verify(raw: bytes, eid: str):
    replay = json.loads(raw)
    if str(replay["info"]["EpisodeId"]) != eid or len(replay["steps"]) != 720:
        raise ValueError(f"episode {eid}: wrong ID or step count")
    return {"episode_id": eid, "sha256": hashlib.sha256(raw).hexdigest(),
            "raw_bytes": len(raw), "teams": replay["info"]["TeamNames"],
            "rewards": replay["rewards"], "statuses": replay["statuses"]}


for index, eid in enumerate(MANIFEST["episodes"], 1):
    final = DEST / f"episode-{eid}-replay.json.gz"
    if final.exists():
        continue
    raw_path = DEST / f"episode-{eid}-replay.json"
    old_path = OLD / f"episode-{eid}-replay.json"
    if old_path.exists():
        raw = old_path.read_bytes()
        origin = "prior_top20_corpus"
    else:
        for attempt in range(10):
            try:
                if not raw_path.exists():
                    api.competition_episode_replay(int(eid), path=str(DEST), quiet=True)
                raw = raw_path.read_bytes()
                origin = "kaggle_public_replay"
                break
            except Exception as exc:
                if raw_path.exists():
                    raw_path.unlink()
                delay = min(10 * (attempt + 1), 90) if "429" in str(exc) else min(3 * (attempt + 1), 30)
                print(f"episode {eid} attempt {attempt+1}: {exc}; wait {delay}s", flush=True)
                time.sleep(delay)
        else:
            print(f"FAILED episode {eid}", flush=True)
            continue
    try:
        record = verify(raw, eid)
        record.update(origin=origin, split=MANIFEST["episodes"][eid]["split"],
                      source_ranks=MANIFEST["episodes"][eid]["source_ranks"])
        temp = final.with_suffix(".json.gz.tmp")
        with gzip.open(temp, "wb", compresslevel=4) as stream:
            stream.write(raw)
        os.replace(temp, final)
        record["compressed_bytes"] = final.stat().st_size
        with AUDIT.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
        if raw_path.exists():
            raw_path.unlink()
        if index % 10 == 0 or index == len(MANIFEST["episodes"]):
            print(f"verified {index}/{len(MANIFEST['episodes'])}: {eid}", flush=True)
        if origin != "prior_top20_corpus":
            time.sleep(0.3)
    except Exception as exc:
        print(f"INVALID episode {eid}: {exc}", flush=True)
