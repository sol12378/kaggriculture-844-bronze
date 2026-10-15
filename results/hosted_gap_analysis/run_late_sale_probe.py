"""Screen late-sale probes against fixed actions from selected hosted games."""
import contextlib
import copy
import io
import json
from pathlib import Path

from kaggle_environments import make

HERE = Path(__file__).resolve().parent
IDS = (115714184, 115748361, 115739060, 115703354, 115740605,
       115749923, 115717256, 115721958, 115712634)
VARIANTS = ("late_unprotect", "late_unprotect_look5")
rows = []
for episode_id in IDS:
    data = json.loads((HERE / "replays" / f"episode-{episode_id}-replay.json").read_text(encoding="utf-8"))
    seat = data["info"]["TeamNames"].index("sol12378")
    other = 1-seat
    tape = [(s[other].get("action") or {"farmer": ["PASS"], "hands": [], "market": []}) for s in data["steps"][1:]]

    def opponent(observation, configuration):
        t = observation["step"]
        return copy.deepcopy(tape[t]) if 0 <= t < len(tape) else {"farmer": ["PASS"], "hands": [], "market": []}

    config = dict(data["configuration"])
    config["seed"] = data["info"]["seed"]
    original_margin = data["rewards"][seat]-data["rewards"][other]
    for variant in VARIANTS:
        path = HERE / "probes" / variant / "main.py"
        agents = [str(path), opponent] if seat == 0 else [opponent, str(path)]
        log = io.StringIO()
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            env = make("kaggriculture", configuration=config)
            final = env.run(agents)[-1]
        margin = final[seat]["reward"] - final[other]["reward"]
        row = {"episode_id":episode_id,"variant":variant,"seed":config["seed"],"seat":seat,
               "original_margin":original_margin,"margin":margin,"delta":margin-original_margin,
               "status":final[seat]["status"],"steps":len(env.steps),"log_excerpt":log.getvalue()[:200]}
        rows.append(row)
        (HERE / "LATE_PROBE_SCREEN.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(json.dumps(row),flush=True)
