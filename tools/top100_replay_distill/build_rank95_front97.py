"""Add the public rank97 market timing hypothesis to the rank95 route."""
import base64
import json
import runpy
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
base = HERE / "candidates" / "rank95_basic" / "main.py"
source = base.read_text(encoding="utf-8")
plan = runpy.run_path(str(HERE / "candidates" / "rank97_basic" / "main.py"))["_DISTILLED_ROUTE"]
blob = base64.b85encode(zlib.compress(json.dumps(plan, separators=(",", ":")).encode(), 9)).decode()
code = source.replace("'front_run': False", "'front_run': True")
code = code.replace("agent = make_agent({0: _DISTILLED_ROUTE}, **_DISTILLED_SETTINGS)",
                    f"_OPPONENT_PLAN = json.loads(zlib.decompress(base64.b85decode({blob!r})))\n"
                    "agent = make_agent({0: _DISTILLED_ROUTE}, opponent_plan=_OPPONENT_PLAN, **_DISTILLED_SETTINGS)")
assert code != source
out = HERE / "candidates" / "rank95_front97"
out.mkdir(parents=True, exist_ok=True)
(out / "main.py").write_text(code, encoding="utf-8")
(out / "PROVENANCE.json").write_text(json.dumps({"parent": "rank95_basic",
    "opponent_plan": "rank97_basic development replay", "mechanism": "bounded public-plan market anticipation"},
    indent=2), encoding="utf-8")
print(out / "main.py", len(code))
