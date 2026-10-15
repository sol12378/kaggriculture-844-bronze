"""Combine same-opening top-100 routes at first public shop reveal (step 72)."""

import base64
import json
import runpy
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sources = {
    "default": HERE / "candidates" / "rank88_c_full" / "main.py",
    "ice_cream": HERE / "candidates" / "rank88_a_basic" / "main.py",
    "yarn": HERE / "candidates" / "rank88_b_basic" / "main.py",
}
routes = {name: runpy.run_path(str(path))["_DISTILLED_ROUTE"] for name, path in sources.items()}
for name, route in routes.items():
    assert len(route) == 719
    assert all(route[s]["farmer"] == routes["default"][s]["farmer"]
               and route[s]["hands"] == routes["default"][s]["hands"]
               for s in range(72)), f"{name}: pre-shop production action mismatch"
source = sources["default"].read_text(encoding="utf-8")
chassis_source = source.split("\nimport base64, json, zlib\n", 1)[0]
settings = runpy.run_path(str(sources["default"]))["_DISTILLED_SETTINGS"]
for with_yarn in (False, True):
    name = "shop_hybrid_ice_yarn" if with_yarn else "shop_hybrid_ice"
    out = HERE / "candidates" / name
    out.mkdir(parents=True, exist_ok=True)
    chosen = [routes["default"], routes["ice_cream"]] + ([routes["yarn"]] if with_yarn else [])
    blobs = [base64.b85encode(zlib.compress(json.dumps(r, separators=(",", ":")).encode(), 9)).decode()
             for r in chosen]
    code = (chassis_source + "\nimport base64, json, zlib\n"
            + f"_BLOBS = {blobs!r}\n"
            + "_ROUTES = {i: json.loads(zlib.decompress(base64.b85decode(blob))) for i, blob in enumerate(_BLOBS)}\n"
            + f"_DISTILLED_SETTINGS = {settings!r}\n"
            + "def _shop_router(observation, step, state):\n"
            + "    if step < 72: return 0\n"
            + "    if 'route' not in state:\n"
            + "        shops = observation.get('town', {}).get('unlocked_shops', [])\n"
            + "        first = shops[0] if shops else None\n"
            + "        state['route'] = 1 if first == 'ICE_CREAM_SHOP' else "
            + ("2 if first == 'YARN_STORE' else 0\n" if with_yarn else "0\n")
            + "    return state['route']\n"
            + "agent = make_agent(_ROUTES, router=_shop_router, **_DISTILLED_SETTINGS)\n"
            + "submission_agent = agent\n")
    (out / "main.py").write_text(code, encoding="utf-8")
    (out / "PROVENANCE.json").write_text(json.dumps({"sources": {k: str(v.relative_to(HERE)) for k,v in sources.items()},
        "switch_step": 72, "with_yarn": with_yarn, "uses_only_development_replays": True}, indent=2), encoding="utf-8")
    print(name, len(code), "bytes")
