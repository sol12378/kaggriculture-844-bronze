"""Extract a local archive and exercise its actual path-loaded Kaggle entrypoint."""

import argparse
import contextlib
import hashlib
import io
import json
import tarfile
from pathlib import Path

from kaggle_environments import make

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
parser = argparse.ArgumentParser()
parser.add_argument("candidate")
args = parser.parse_args()
folder = HERE / "candidates" / args.candidate
audit = json.loads((folder / "PACKAGE_AUDIT.json").read_text(encoding="utf-8"))
archive = folder / "submission.tar.gz"
assert hashlib.sha256(archive.read_bytes()).hexdigest() == audit["archive_sha256"]
dest = folder / "validation_extracted"
dest.mkdir(exist_ok=True)
with tarfile.open(archive, "r:gz") as stream:
    assert stream.getnames() == ["main.py", "LICENSE", "NOTICE"]
    for member in stream.getmembers():
        assert member.isfile() and member.name in audit["members"]
        payload = stream.extractfile(member).read()
        assert hashlib.sha256(payload).hexdigest() == audit["members"][member.name]["sha256"]
        (dest / member.name).write_bytes(payload)
rows = []
for seat in (0, 1):
    seed = 25330001 + seat
    files = [str(dest / "main.py"), str(ROOT / "top20_counter_20260930" / "main.py")]
    if seat:
        files.reverse()
    log = io.StringIO()
    with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
        final = env.run(files)[-1]
    rows.append({"seat": seat, "seed": seed, "status": final[seat]["status"],
                 "candidate_reward": final[seat]["reward"],
                 "baseline_reward": final[1-seat]["reward"],
                 "steps": len(env.steps), "log_excerpt": log.getvalue()[:200]})
assert all(r["status"] == "DONE" and r["candidate_reward"] > 3000 for r in rows)
result = {"candidate": args.candidate, "archive_sha256": audit["archive_sha256"],
          "engine": "official kaggle_environments 1.32.7 path loader", "rows": rows}
(folder / "ARCHIVE_PATH_VALIDATION.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result))
