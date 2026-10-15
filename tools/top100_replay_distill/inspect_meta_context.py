"""Inspect public information available at the first shop unlock."""
import json
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "kg373_gold_20260922" / "fast_sim" / "upstream_cppsim"))
import kagsim

candidate = runpy.run_path(str(ROOT / "top100_replay_distill_20260930" / "candidates" / "rank88_c_full" / "main.py"))["agent"]
baseline = runpy.run_path(str(ROOT / "top20_counter_20260930" / "main.py"))["agent"]
game = kagsim.Game(26330001)
for _ in range(72):
    game.step(candidate(game.observe(0)), baseline(game.observe(1)))
obs = game.observe(0)
print(json.dumps({k: obs[k] for k in ("step", "player", "town", "farms", "market") if k in obs}, ensure_ascii=False, indent=2)[:12000])
