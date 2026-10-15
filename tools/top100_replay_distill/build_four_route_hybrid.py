"""Fit a compact shop-conditional router from four compatible public routes."""

import base64
import json
import runpy
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
names = ("rank88_c_full", "rank88_a_basic", "rank88_b_basic", "rank97_basic")
sources = [HERE / "candidates" / n / "main.py" for n in names]
routes = [runpy.run_path(str(path))["_DISTILLED_ROUTE"] for path in sources]
assert all(len(route) == 719 for route in routes)
chassis = sources[0].read_text(encoding="utf-8").split("\nimport base64, json, zlib\n", 1)[0]
settings = runpy.run_path(str(sources[0]))["_DISTILLED_SETTINGS"]
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
        + "        first = shops[0] if shops else None\n"
        + "        state['route'] = (1 if first in ('ICE_CREAM_SHOP', 'SMOOTHIE_SHOP')\n"
        + "                          else 2 if first == 'YARN_STORE'\n"
        + "                          else 3 if first == 'PIZZA_SHOP' else 0)\n"
        + "    return state['route']\n"
        + "agent = make_agent(_ROUTES, router=_shop_router, **_DISTILLED_SETTINGS)\n"
        + "submission_agent = agent\n")
out = HERE / "candidates" / "shop_hybrid_four"
out.mkdir(parents=True, exist_ok=True)
(out / "main.py").write_text(code, encoding="utf-8")
(out / "PROVENANCE.json").write_text(json.dumps({"route_sources": list(names),
    "switch_step": 72, "selection": {"ICE_CREAM_SHOP": 1, "SMOOTHIE_SHOP": 1,
                                 "YARN_STORE": 2, "PIZZA_SHOP": 3, "default": 0},
    "physical_state_compatibility": "64/64 seeds at step72; rank97 route differs by 4 coins only",
    "uses_only_development_replays": True}, indent=2), encoding="utf-8")
print(out / "main.py", len(code), "bytes")
