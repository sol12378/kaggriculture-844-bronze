"""Replay a hosted opponent's issued actions in the official local engine.

This is a fixed-action counterfactual, not a live opponent policy test.
"""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys

from kaggle_environments import make

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
FIRST = ROOT / "top20_counter_20260930" / "main.py"
SECOND = ROOT / "second_meta_agent_20260930" / "main.py"
if sys.argv[1:2] in (["losses"], ["wins"], ["all"], ["new"]):
    mode = sys.argv[1]
    episode_rows = json.loads((HERE / "HOSTED_EPISODES.json").read_text(encoding="utf-8"))
    already = set()
    if mode == "new":
        for old in ("TAPE_COUNTERFACTUAL_LOSSES.json", "TAPE_COUNTERFACTUAL_WINS.json"):
            already.update(r["episode_id"] for r in json.loads((HERE / old).read_text(encoding="utf-8")))
    IDS = [r["episode_id"] for r in episode_rows
           if r["type"] == "EPISODE_TYPE_PUBLIC" and r["outcome"]
           and (mode in ("all", "new") or r["outcome"] == ("loss" if mode == "losses" else "win"))
           and r["episode_id"] not in already]
    output = HERE / f"TAPE_COUNTERFACTUAL_{mode.upper()}.json"
else:
    mode = "sample"
    IDS = [int(x) for x in sys.argv[1:]] or [115748361]
    output = HERE / "TAPE_COUNTERFACTUAL.json"
rows = []
for episode_id in IDS:
    data = json.loads((HERE / "replays" / f"episode-{episode_id}-replay.json").read_text(encoding="utf-8"))
    seat = data["info"]["TeamNames"].index("sol12378")
    other = 1 - seat
    tape = [(s[other].get("action") or {"farmer": ["PASS"], "hands": [], "market": []}) for s in data["steps"][1:]]

    def opponent(observation, configuration):
        step = observation["step"]
        return copy.deepcopy(tape[step]) if 0 <= step < len(tape) else {"farmer": ["PASS"], "hands": [], "market": []}

    config = dict(data["configuration"])
    config["seed"] = data["info"]["seed"]
    candidates = (("second_h5", SECOND),) if mode == "wins" else (("first", FIRST), ("second_h5", SECOND))
    for label, candidate in candidates:
        agents = [str(candidate), opponent] if seat == 0 else [opponent, str(candidate)]
        log = io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            env = make("kaggriculture", configuration=config)
            final = env.run(agents)[-1]
        row = {"episode_id": episode_id, "candidate": label, "seed": config["seed"], "seat": seat,
               "recorded_reward": data["rewards"][seat], "recorded_opponent_reward": data["rewards"][other],
               "reward": final[seat]["reward"], "opponent_reward": final[other]["reward"],
               "status": final[seat]["status"], "steps": len(env.steps),
               "log_excerpt": log.getvalue()[:300]}
        rows.append(row)
        print(json.dumps(row), flush=True)
        output.write_text(json.dumps(rows, indent=2), encoding="utf-8")
