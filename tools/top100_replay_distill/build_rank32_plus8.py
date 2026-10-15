"""Test the rank32 route with the compatible, higher-cash rank88 opening."""
import base64
import json
import runpy
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
names = ("rank88_c_full", "rank32_screen")
paths = [HERE / "candidates" / n / "main.py" for n in names]
routes = [runpy.run_path(str(p))["_DISTILLED_ROUTE"] for p in paths]
chassis = paths[0].read_text(encoding="utf-8").split("\nimport base64, json, zlib\n", 1)[0]
settings = runpy.run_path(str(paths[0]))["_DISTILLED_SETTINGS"]
blobs = [base64.b85encode(zlib.compress(json.dumps(r, separators=(",", ":")).encode(), 9)).decode()
         for r in routes]
code = (chassis + "\nimport base64, json, zlib\n"
        + f"_BLOBS = {blobs!r}\n"
        + "_ROUTES = {i: json.loads(zlib.decompress(base64.b85decode(blob))) for i, blob in enumerate(_BLOBS)}\n"
        + f"_DISTILLED_SETTINGS = {settings!r}\n"
        + "def _route(observation, step, state):\n"
        + "    return 0 if step < 72 else 1\n"
        + "agent = make_agent(_ROUTES, router=_route, **_DISTILLED_SETTINGS)\n"
        + "submission_agent = agent\n")
out = HERE / "candidates" / "rank32_plus8"
out.mkdir(parents=True, exist_ok=True)
(out / "main.py").write_text(code, encoding="utf-8")
(out / "PROVENANCE.json").write_text(json.dumps({"opening": names[0], "continuation": names[1],
    "switch_step": 72, "physical_compatibility": "31/32 fresh seeds at step72",
    "cash_difference": "rank88 opening +8 on all 32 seeds", "uses_only_development_replays": True},
    indent=2), encoding="utf-8")
print(out / "main.py", len(code))

front = HERE / "candidates" / "rank32_plus8_front97"
front.mkdir(parents=True, exist_ok=True)
rank97 = runpy.run_path(str(HERE / "candidates" / "rank97_basic" / "main.py"))["_DISTILLED_ROUTE"]
rank97_blob = base64.b85encode(zlib.compress(json.dumps(rank97, separators=(",", ":")).encode(), 9)).decode()
front_code = code.replace("'front_run': False", "'front_run': True")
front_code = front_code.replace(
    "agent = make_agent(_ROUTES, router=_route, **_DISTILLED_SETTINGS)",
    f"_OPPONENT_PLAN = json.loads(zlib.decompress(base64.b85decode({rank97_blob!r})))\n"
    "agent = make_agent(_ROUTES, router=_route, opponent_plan=_OPPONENT_PLAN, **_DISTILLED_SETTINGS)")
assert front_code != code
(front / "main.py").write_text(front_code, encoding="utf-8")
(front / "PROVENANCE.json").write_text(json.dumps({"parent": "rank32_plus8",
    "opponent_plan": "rank97_basic development replay", "mechanism": "bounded public-plan market anticipation"},
    indent=2), encoding="utf-8")
print(front / "main.py", len(front_code))
