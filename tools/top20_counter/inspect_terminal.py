"""Inspect one official match's endgame state and order divergence."""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

from kaggle_environments import make

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / "ready_2500_final_20260930/main.py"
V4 = ROOT / "submission_ready_20260930/main.py"
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 15100203})
    final = env.run([str(BASE), str(V4)])[-1]
rows = []
for step in range(672, 719):
    own = env.steps[step][0]["observation"]
    other = env.steps[step][1]["observation"]
    a = env.steps[step + 1][0].get("action") or {}
    b = env.steps[step + 1][1].get("action") or {}
    row = {
        "step": step,
        "money": [own["farms"][0]["money"], own["farms"][1]["money"]],
        "shed": [own["private"]["shed"], other["private"]["shed"]],
        "inventory": [own["private"]["inventories"], other["private"]["inventories"]],
        "market": [a.get("market"), b.get("market")],
    }
    rows.append(row)
summary = {"seed": 15100203, "rewards": [f["reward"] for f in final], "rows": rows}
(HERE / "TERMINAL_15100203.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
for row in rows:
    m = row["money"]
    print(row["step"], m[0]-m[1],
          sum(row["shed"][0].values()), sum(row["shed"][1].values()),
          row["market"][0], row["market"][1], flush=True)
