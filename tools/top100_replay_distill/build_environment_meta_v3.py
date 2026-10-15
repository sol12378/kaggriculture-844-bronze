"""Combine the two strongest compatible continuations by first public shop."""
import base64
import json
import runpy
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
names = ("rank88_c_full", "rank97_basic", "rank32_screen")
paths = [HERE / "candidates" / name / "main.py" for name in names]
routes = [runpy.run_path(str(path))["_DISTILLED_ROUTE"] for path in paths]
chassis = paths[0].read_text(encoding="utf-8").split("\nimport base64, json, zlib\n", 1)[0]
settings = runpy.run_path(str(paths[0]))["_DISTILLED_SETTINGS"]
settings["front_run"] = True
blobs = [base64.b85encode(zlib.compress(json.dumps(r, separators=(",", ":")).encode(), 9)).decode()
         for r in routes]
code = (chassis + "\nimport base64, json, zlib\n"
        + f"_BLOBS = {blobs!r}\n"
        + "_ROUTES = {i: json.loads(zlib.decompress(base64.b85decode(blob))) for i, blob in enumerate(_BLOBS)}\n"
        + f"_DISTILLED_SETTINGS = {settings!r}\n"
        + "def _shop_router(observation, step, state):\n"
        + "    if step < 72: return 0\n"
        + "    if 'route' not in state:\n"
        + "        shops = observation.get('town', {}).get('unlocked_shops', [])\n"
        + "        state['route'] = 2 if shops and shops[0] in ('FARMERS_MARKET', 'PIZZA_SHOP') else 1\n"
        + "    return state['route']\n"
        + "agent = make_agent(_ROUTES, router=_shop_router, opponent_plan=_ROUTES[1], **_DISTILLED_SETTINGS)\n"
        + "submission_agent = agent\n")
out = HERE / "candidates" / "environment_meta_shop_v3"
out.mkdir(parents=True, exist_ok=True)
(out / "main.py").write_text(code, encoding="utf-8")
(out / "PROVENANCE.json").write_text(json.dumps({"route_sources": names,
    "selection_training": "TOP2_SHOP_EFFECT.json from two official seed families",
    "first_shop_selection": {"FARMERS_MARKET": "rank32_screen", "PIZZA_SHOP": "rank32_screen",
                             "default": "rank97_basic"},
    "switch_step": 72, "public_inputs": ["first unlocked town shop"],
    "opponent_plan": "rank97_basic public development replay",
    "validation_plan": "fresh 40330001 family; live official engine; both seats"}, indent=2), encoding="utf-8")
print(out / "main.py", len(code))
