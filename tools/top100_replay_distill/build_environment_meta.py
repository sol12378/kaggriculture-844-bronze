"""Build a public-observation route selector from development matchups."""
import base64
import json
import runpy
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
names = ("rank88_c_full", "rank97_basic")
sources = [HERE / "candidates" / name / "main.py" for name in names]
routes = [runpy.run_path(str(source))["_DISTILLED_ROUTE"] for source in sources]
assert all(len(route) == 719 for route in routes)
chassis = sources[0].read_text(encoding="utf-8").split("\nimport base64, json, zlib\n", 1)[0]
settings = runpy.run_path(str(sources[0]))["_DISTILLED_SETTINGS"]
blobs = [base64.b85encode(zlib.compress(json.dumps(route, separators=(",", ":")).encode(), 9)).decode()
         for route in routes]
code = (chassis + "\nimport base64, json, zlib\n"
        + f"_BLOBS = {blobs!r}\n"
        + "_ROUTES = {i: json.loads(zlib.decompress(base64.b85decode(blob))) for i, blob in enumerate(_BLOBS)}\n"
        + f"_DISTILLED_SETTINGS = {settings!r}\n"
        + "def _environment_router(observation, step, state):\n"
        + "    if step < 72: return 0\n"
        + "    if 'route' not in state:\n"
        + "        shops = observation.get('town', {}).get('unlocked_shops', [])\n"
        + "        shop = shops[0] if shops else None\n"
        + "        farms = observation.get('farms', [])\n"
        + "        other = 1 - int(observation.get('player', 0))\n"
        + "        rival = farms[other] if len(farms) > other else {}\n"
        + "        sheep = sum(tile.get('animal') == 'SHEEP'\n"
        + "                    for row in rival.get('tiles', []) for tile in row\n"
        + "                    if isinstance(tile, dict) and tile.get('kind') == 'PASTURE')\n"
        + "        state['route'] = 0 if shop in ('PIZZA_SHOP', 'BRUNCH_SPOT') and sheep < 3 else 1\n"
        + "    return state['route']\n"
        + "agent = make_agent(_ROUTES, router=_environment_router, **_DISTILLED_SETTINGS)\n"
        + "submission_agent = agent\n")
out = HERE / "candidates" / "environment_meta_v1"
out.mkdir(parents=True, exist_ok=True)
(out / "main.py").write_text(code, encoding="utf-8")
(out / "PROVENANCE.json").write_text(json.dumps({"source_routes": names,
    "training_data": "ENV_TRAIN_26330001_16.json", "switch_step": 72,
    "public_inputs": ["first unlocked town shop", "rival sheep count on public farm"],
    "rule": "choose rank88c for BRUNCH or PIZZA against rivals with fewer than 3 sheep; rank97 otherwise",
    "route_compatibility": "64/64 physical states identical at step72; rank97 cash differs by 4",
    "uses_only_development_replays": True}, indent=2), encoding="utf-8")
print(out / "main.py", len(code), "bytes")

# Ablation control: same four-coin opening, always switch to the rank97 route.
# Comparing against this control isolates the value of environmental routing.
control = HERE / "candidates" / "rank97_plus4"
control.mkdir(parents=True, exist_ok=True)
control_code = code.replace(
    "state['route'] = 0 if shop in ('PIZZA_SHOP', 'BRUNCH_SPOT') and sheep < 3 else 1",
    "state['route'] = 1")
assert control_code != code
(control / "main.py").write_text(control_code, encoding="utf-8")
(control / "PROVENANCE.json").write_text(json.dumps({"source_routes": names,
    "role": "ablation control for environment_meta_v1", "switch_step": 72,
    "rule": "rank88c opening, rank97 thereafter regardless of environment",
    "uses_only_development_replays": True}, indent=2), encoding="utf-8")
print(control / "main.py", len(control_code), "bytes")

# Public-replay market anticipation: test both rival schedules as a hypothesis.
# The front-run layer only advances sales of stock already held and planned for
# the next action; it does not inspect private opponent inventory or actions.
for plan_id, suffix in ((0, "88"), (1, "97")):
    variant = HERE / "candidates" / f"environment_meta_front_{suffix}"
    variant.mkdir(parents=True, exist_ok=True)
    variant_code = code.replace("'front_run': False", "'front_run': True")
    variant_code = variant_code.replace(
        "agent = make_agent(_ROUTES, router=_environment_router, **_DISTILLED_SETTINGS)",
        f"agent = make_agent(_ROUTES, router=_environment_router, opponent_plan=_ROUTES[{plan_id}], **_DISTILLED_SETTINGS)")
    assert variant_code != code
    (variant / "main.py").write_text(variant_code, encoding="utf-8")
    (variant / "PROVENANCE.json").write_text(json.dumps({"parent": "environment_meta_v1",
        "opponent_plan": names[plan_id], "source": "development public replay",
        "mechanism": "advance bounded own sales when public plan predicts a next-step sell"}, indent=2), encoding="utf-8")
    print(variant / "main.py", len(variant_code), "bytes")
