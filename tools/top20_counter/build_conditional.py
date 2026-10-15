"""Build the conditional top-20 replay repair plus opening market edge."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "candidate_cow_fert_care_water/main.py"
EXPECTED_SOURCE_SHA = "2048c6433b6428c70c22ca76674e46308873e5c64bece71c24e8f6f13ae35a25"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SOURCE_SHA

ADDENDUM = r'''

# Conditional opening guard. The parent's equal-money branch uses an 8-unit
# wheat buy/sell round trip on turns 1/2. The official price curve rounds
# per-unit quotes; 4 units preserve the branch and gain four coins against the
# same opening in the frozen development and holdout panels. For this matched
# opening we leave the long route untouched. Against different openings, the
# replay-guided worker repair above remains active.
_COND_PARENT = _TOP20_PARENT
_COND_MIRROR = {{0: False, 1: False}}

def agent(observation, configuration=None):
    action = _COND_PARENT(observation, configuration)
    try:
        step = int(observation["step"])
        seat = int(observation["player"])
        if step == 0:
            _COND_MIRROR[seat] = False
        if step in (1, 2) and isinstance(action, dict):
            market = [list(order) for order in (action.get("market") or [])]
            if step == 1 and market and market[0] == ["BUY_PRODUCT", "WHEAT", 8]:
                _COND_MIRROR[seat] = True
                market[0] = ["BUY_PRODUCT", "WHEAT", 4]
                action = dict(action, market=market)
            elif step == 2 and _COND_MIRROR.get(seat) and market and market[0] == ["SELL", "WHEAT", 8]:
                market[0] = ["SELL", "WHEAT", 4]
                action = dict(action, market=market)
        if _COND_MIRROR.get(seat):
            return action
        return _top20_repair(observation, action)
    except Exception:
        return action

# A newly inserted unique callable is required by kaggle_environments 1.32.7.
submission_agent_conditional = agent
'''.replace("{{", "{").replace("}}", "}")

folder = HERE / "candidate_conditional"
folder.mkdir(exist_ok=True)
contents = SOURCE.read_text(encoding="utf-8") + ADDENDUM
compile(contents, str(folder / "main.py"), "exec")
(folder / "main.py").write_text(contents, encoding="utf-8")
shutil.copyfile(HERE / "candidate_cow_fert_care_water/LICENSE", folder / "LICENSE")
(folder / "NOTICE").write_text(
    (HERE / "candidate_cow_fert_care_water/NOTICE").read_text(encoding="utf-8")
    + "Original equal-opening wheat quantity guard appended by this project.\n",
    encoding="utf-8",
)
report = {"base_candidate_sha256": EXPECTED_SOURCE_SHA,
          "conditional_main_sha256": hashlib.sha256((folder / "main.py").read_bytes()).hexdigest(),
          "last_unique_callable": "submission_agent_conditional",
          "submission_performed": False}
(HERE / "CONDITIONAL_BUILD_AUDIT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
