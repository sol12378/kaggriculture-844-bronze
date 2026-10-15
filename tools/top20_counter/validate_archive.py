"""Verify the final archive through Kaggle's actual Python file loader."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import tarfile
from pathlib import Path

from kaggle_environments import make

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
archive = HERE / "submission.tar.gz"
expected_archive = "170a7dbd489362738844efbeae04a24114f8a427437dd7788a94c070d8d2b36d"
expected_main = "f7f6a0c330c585a71c4854a34c02d922e20c68fa0006ff00ebe82d9528562220"
assert hashlib.sha256(archive.read_bytes()).hexdigest() == expected_archive
with tarfile.open(archive, "r:gz") as tar:
    assert [member.name for member in tar.getmembers()] == ["main.py", "LICENSE", "NOTICE"]
    main = tar.extractfile("main.py").read()
assert hashlib.sha256(main).hexdigest() == expected_main
extract_dir = HERE / "archive_extracted"
extract_dir.mkdir(exist_ok=True)
path = extract_dir / "main.py"
path.write_bytes(main)

rows = []
for label, opponent in (
    ("public_parent", ROOT / "ready_2500_final_20260930/main.py"),
    ("local_v4", ROOT / "submission_ready_20260930/main.py"),
):
    for seat in (0, 1):
        players = [str(path), str(opponent)] if seat == 0 else [str(opponent), str(path)]
        log = io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 21200011})
            final = env.run(players)[-1]
        first = env.steps[1][seat].get("action")
        active = sum(
            isinstance(action, dict)
            and (bool(action.get("market")) or action.get("farmer") != ["PASS"] or bool(action.get("hands")))
            for action in (step[seat].get("action") for step in env.steps[1:])
        )
        row = {"opponent": label, "seat": seat,
               "status": final[seat]["status"], "game_steps": len(env.steps),
               "reward": final[seat]["reward"], "opponent_reward": final[1-seat]["reward"],
               "first_action": first, "active_turns": active,
               "loader_fallback": not isinstance(first, dict) or "__raw_path__" in first,
               "log_excerpt": log.getvalue()[:200]}
        assert row["status"] == "DONE" and row["game_steps"] == 720
        assert active == 719 and not row["loader_fallback"] and first.get("market")
        rows.append(row)
        print(label, seat, row["reward"], row["opponent_reward"], flush=True)
report = {"engine": "kaggle-environments 1.32.7", "archive_sha256": expected_archive,
          "method": "extract archive then pass main.py path to env.run", "games": rows,
          "submission_performed": False}
(HERE / "ARCHIVE_PATH_VALIDATION.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
