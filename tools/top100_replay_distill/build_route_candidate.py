"""Make a state-guarded route prototype from a public top-100 trajectory."""

import argparse
import base64
import gzip
import json
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
parser = argparse.ArgumentParser()
parser.add_argument("--rank", type=int, required=True)
parser.add_argument("--episode", required=True)
parser.add_argument("--name", required=True)
parser.add_argument("--guards", choices=("basic", "full"), default="basic")
args = parser.parse_args()
assert 1 <= args.rank <= 100
assert args.name.replace("_", "").isalnum()
manifest = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
target = manifest["ranks"][str(args.rank)]
assert args.episode in target["development_ids"], "candidate route must be development split"
with gzip.open(HERE / "replays" / f"episode-{args.episode}-replay.json.gz", "rt", encoding="utf-8") as stream:
    replay = json.load(stream)
seat = next(i for i, a in enumerate(manifest["episodes"][args.episode]["agents"])
            if a["submissionId"] == target["submission_id"] and a["teamId"] == target["team_id"])
actions = [replay["steps"][s + 1][seat].get("action") for s in range(719)]
assert all(isinstance(a, dict) for a in actions)
source = (ROOT / "top20_counter_20260930" / "main.py").read_text(encoding="utf-8")
marker = "\nimport base64\nimport json\nimport zlib\n_R108_DATA"
assert marker in source
chassis_source = source.split(marker, 1)[0]
blob = base64.b85encode(zlib.compress(json.dumps(actions, separators=(",", ":")).encode(), 9)).decode()
settings = {"hand_align": True, "weed_repair": True, "sell_lead": True,
            "front_run": False, "budget_guard": args.guards == "full",
            "room_guard": args.guards == "full", "clamp_sells": args.guards == "full",
            "dead_stock": args.guards == "full", "terminal_liquidation": True}
output = HERE / "candidates" / args.name
output.mkdir(parents=True, exist_ok=True)
code = (chassis_source + "\nimport base64, json, zlib\n"
        + f"_DISTILLED_ROUTE = json.loads(zlib.decompress(base64.b85decode({blob!r})))\n"
        + f"_DISTILLED_SETTINGS = {settings!r}\n"
        + "agent = make_agent({0: _DISTILLED_ROUTE}, **_DISTILLED_SETTINGS)\n"
        + "submission_agent = agent\n")
(output / "main.py").write_text(code, encoding="utf-8")
(output / "PROVENANCE.json").write_text(json.dumps({"rank": args.rank, "team_id": target["team_id"],
    "submission_id": target["submission_id"], "episode_id": args.episode, "seat": seat,
    "split": "development", "guards": args.guards,
    "note": "Public action trajectory used as guarded route; no source code or private opponent data included"},
    indent=2), encoding="utf-8")
print(output / "main.py", len(code), "bytes")
