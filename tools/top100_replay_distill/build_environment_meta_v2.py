"""Fit rank32 route into the public shop/opponent-opening selector."""
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
blobs = [base64.b85encode(zlib.compress(json.dumps(r, separators=(",", ":")).encode(), 9)).decode()
         for r in routes]
header = (chassis + "\nimport base64, json, zlib\n"
          + f"_BLOBS = {blobs!r}\n"
          + "_ROUTES = {i: json.loads(zlib.decompress(base64.b85decode(blob))) for i, blob in enumerate(_BLOBS)}\n"
          + f"_DISTILLED_SETTINGS = {settings!r}\n"
          + "def _environment_router(observation, step, state):\n"
          + "    if step < 72: return 0\n"
          + "    if 'route' not in state:\n"
          + "        shops = observation.get('town', {}).get('unlocked_shops', [])\n"
          + "        shop = shops[0] if shops else None\n"
          + "        farms = observation.get('farms', [])\n"
          + "        player = int(observation.get('player', 0))\n"
          + "        mine = farms[player] if len(farms) > player else {}\n"
          + "        other = 1-player\n"
          + "        rival = farms[other] if len(farms) > other else {}\n"
          + "        sheep = sum(tile.get('animal') == 'SHEEP'\n"
          + "                    for row in rival.get('tiles', []) for tile in row\n"
          + "                    if isinstance(tile, dict) and tile.get('kind') == 'PASTURE')\n"
          + "        cash_delta = float(mine.get('money', 0)) - float(rival.get('money', 0))\n"
          + "        if shop in ('FARMERS_MARKET', 'ICE_CREAM_SHOP') and sheep >= 3 and 0 < cash_delta < 10:\n"
          + "            state['route'] = 2\n"
          + "        elif shop in ('PIZZA_SHOP', 'BRUNCH_SPOT') and sheep < 3:\n"
          + "            state['route'] = 0\n"
          + "        else:\n"
          + "            state['route'] = 1\n"
          + "    return state['route']\n")

for front in (False, True):
    code = header
    if front:
        code = code.replace("'front_run': False", "'front_run': True")
        code += "agent = make_agent(_ROUTES, router=_environment_router, opponent_plan=_ROUTES[1], **_DISTILLED_SETTINGS)\n"
    else:
        code += "agent = make_agent(_ROUTES, router=_environment_router, **_DISTILLED_SETTINGS)\n"
    code += "submission_agent = agent\n"
    name = "environment_meta_v2_front97" if front else "environment_meta_v2"
    out = HERE / "candidates" / name
    out.mkdir(parents=True, exist_ok=True)
    (out / "main.py").write_text(code, encoding="utf-8")
    (out / "PROVENANCE.json").write_text(json.dumps({"routes": names,
        "training": ["ENV_TRAIN_26330001_16.json", "RANK32_DEV_27330001_32.json"],
        "switch_step": 72, "public_inputs": ["first shop", "rival sheep", "visible money difference"],
        "front_run_public_plan": front,
        "caveat": "rank32 physical state matched rank88c on 31 of 32 checked seeds"}, indent=2), encoding="utf-8")
    print(out / "main.py", len(code))
