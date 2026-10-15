"""Create an auditable local Kaggle archive. Never calls the submission API."""

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
parser = argparse.ArgumentParser()
parser.add_argument("candidate")
args = parser.parse_args()
folder = HERE / "candidates" / args.candidate
source = folder / "main.py"
assert source.is_file()
compile(source.read_text(encoding="utf-8"), str(source), "exec")
license_text = (ROOT / "top20_counter_20260930" / "LICENSE").read_bytes()
notice_text = ("Kaggriculture top-100 public replay distilled agent, 2026-09-30.\n"
               "The route-replay chassis is derived from Apache-2.0 public code.\n"
               "Original attribution and license text are retained in main.py and LICENSE.\n"
               "Selected action routes derive from completed public Kaggle replays;\n"
               "no competitor source code, opponent private observation or full replay is included.\n"
               "This archive was prepared locally. It has not been submitted by this script.\n").encode()
(folder / "LICENSE").write_bytes(license_text)
(folder / "NOTICE").write_bytes(notice_text)
archive = folder / "submission.tar.gz"
with tarfile.open(archive, "w:gz") as stream:
    for name in ("main.py", "LICENSE", "NOTICE"):
        data = (folder / name).read_bytes()
        item = tarfile.TarInfo(name)
        item.size = len(data)
        item.mode = 0o644
        item.uid = item.gid = 0
        item.uname = item.gname = ""
        item.mtime = 0
        stream.addfile(item, io.BytesIO(data))
with tarfile.open(archive, "r:gz") as stream:
    members = stream.getnames()
    assert members == ["main.py", "LICENSE", "NOTICE"]
    for member in stream.getmembers():
        assert stream.extractfile(member).read() == (folder / member.name).read_bytes()
audit = {"candidate": args.candidate, "archive": archive.name, "archive_bytes": archive.stat().st_size,
         "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
         "members": {name: {"bytes": (folder / name).stat().st_size,
                            "sha256": hashlib.sha256((folder / name).read_bytes()).hexdigest()}
                     for name in members}, "submitted": False}
(folder / "PACKAGE_AUDIT.json").write_text(json.dumps(audit, indent=2), encoding="utf-8")
print(json.dumps(audit))
