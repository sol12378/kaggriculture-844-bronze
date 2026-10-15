"""Package the exact official-tested candidate without submitting it."""

from __future__ import annotations

import gzip
import hashlib
import io
import json
import shutil
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "candidate_market_small5"
MAIN_SHA = "f7f6a0c330c585a71c4854a34c02d922e20c68fa0006ff00ebe82d9528562220"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


assert digest((SOURCE / "main.py").read_bytes()) == MAIN_SHA
for name in ("main.py", "LICENSE", "NOTICE"):
    shutil.copyfile(SOURCE / name, HERE / name)

archive = HERE / "submission.tar.gz"
with archive.open("wb") as raw:
    with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for name in ("main.py", "LICENSE", "NOTICE"):
                payload = (HERE / name).read_bytes()
                info = tarfile.TarInfo(name)
                info.size = len(payload)
                info.mode = 0o644
                info.mtime = 0
                tar.addfile(info, io.BytesIO(payload))

with tarfile.open(archive, "r:gz") as tar:
    members = tar.getmembers()
    assert [member.name for member in members] == ["main.py", "LICENSE", "NOTICE"]
    assert all(member.isfile() for member in members)
    assert digest(tar.extractfile("main.py").read()) == MAIN_SHA
report = {
    "archive": str(archive),
    "archive_sha256": digest(archive.read_bytes()),
    "main_sha256": MAIN_SHA,
    "archive_members": [member.name for member in members],
    "source_from_official_test": "candidate_market_small5/main.py",
    "last_unique_callable": "submission_agent_market_small5",
    "submission_performed": False,
}
(HERE / "PAYLOAD_AUDIT.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
