"""Build the market-order residual on the conditional replay candidate."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "candidate_conditional/main.py"
SOURCE_SHA = "7ebaf1f05540ed2281cb8320052b37f63c7c3e6ba7b614579253d2cd5cb61b5a"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
ADDENDUM = r'''

# Replay-loss market repair: a prepended small SELL can delay a much larger
# native SELL to the rival's later order slot. Move only a leading <=5-unit
# sale behind other sales when another sale is >=10 units. HIRE/BUY order
# timing, quantities and production remain unchanged. Mirror-opening matches
# retain their verified 4-coin opening edge without this intervention.
_MARKET_PARENT = agent

def agent(observation, configuration=None):
    action = _MARKET_PARENT(observation, configuration)
    try:
        if not isinstance(action, dict) or int(observation["step"]) < 144:
            return action
        seat = int(observation["player"])
        if _COND_MIRROR.get(seat):
            return action
        market = [list(order) for order in (action.get("market") or [])]
        if len(market) < 2 or any(not order or order[0] != "SELL" or len(order) < 3 for order in market):
            return action
        first = market[0]
        if int(first[2]) > 5 or not any(int(order[2]) >= 10 for order in market[1:]):
            return action
        return dict(action, market=market[1:] + [first])
    except Exception:
        return action

# Must be a new namespace key: Kaggle selects the last inserted callable.
submission_agent_market_small5 = agent
'''

folder = HERE / "candidate_market_small5"
folder.mkdir(exist_ok=True)
contents = SOURCE.read_text(encoding="utf-8") + ADDENDUM
compile(contents, str(folder / "main.py"), "exec")
(folder / "main.py").write_text(contents, encoding="utf-8")
shutil.copyfile(HERE / "candidate_conditional/LICENSE", folder / "LICENSE")
(folder / "NOTICE").write_text(
    (HERE / "candidate_conditional/NOTICE").read_text(encoding="utf-8")
    + "Original small-sale slot repair appended by this project.\n",
    encoding="utf-8",
)
report = {"parent_sha256": SOURCE_SHA,
          "main_sha256": hashlib.sha256((folder / "main.py").read_bytes()).hexdigest(),
          "last_unique_callable": "submission_agent_market_small5",
          "submission_performed": False}
(HERE / "MARKET_SMALL5_BUILD_AUDIT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
