"""Summarize hosted cash trajectories and issued action mixes from saved replays."""
from collections import Counter
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = sorted((HERE / "replays").glob("episode-*-replay.json"))

def money(step, seat):
    return step[seat]["observation"]["farms"][seat]["money"]

def features(steps, seat):
    orders = Counter()
    worker = Counter()
    for step in steps[1:]:
        action = step[seat].get("action") or {}
        for order in action.get("market") or []:
            if not order:
                continue
            orders[(order[0], order[1] if len(order) > 1 and isinstance(order[1], str) else "")] += 1
        for order in [action.get("farmer")] + (action.get("hands") or []):
            if order:
                worker[order[0]] += 1
    return {
        "market_orders": {" ".join(k): v for k, v in orders.most_common(20)},
        "worker_actions": dict(worker.most_common(15)),
    }

out = []
for path in FILES:
    data = json.loads(path.read_text(encoding="utf-8"))
    teams = data["info"]["TeamNames"]
    seat = teams.index("sol12378")
    other = 1 - seat
    steps = data["steps"]
    def same_fraction(key):
        pairs = [((step[seat].get("action") or {}).get(key),
                  (step[other].get("action") or {}).get(key)) for step in steps[1:]]
        return round(sum(a == b for a, b in pairs) / len(pairs), 4)
    margins = [money(s, seat) - money(s, other) for s in steps]
    day_marks = {str(day): round(margins[min(719, day * 24 + 23)], 2) for day in (0, 2, 5, 9, 14, 19, 24, 29)}
    large_swings = sorted(
        [(margins[t] - margins[t-1], t) for t in range(1, len(margins))],
        key=lambda x: x[0], reverse=False,
    )[:5]
    swing_rows = [{"step": t, "delta_margin": delta,
                   "our_market": steps[t][seat].get("action", {}).get("market"),
                   "opponent_market": steps[t][other].get("action", {}).get("market")}
                  for delta, t in large_swings]
    first_t = next((t for t, m in enumerate(margins) if m < 0), None)
    final = steps[-1]
    own_farm = final[seat]["observation"]["farms"][seat]
    opponent_farm = final[other]["observation"]["farms"][other]
    def farm_counts(farm):
        return dict(Counter((tile.get("kind") or "OTHER") for row in farm["tiles"]
                            for tile in row if isinstance(tile, dict)))
    out.append({
        "episode": data["info"]["EpisodeId"], "seed": data["info"]["seed"],
        "opponent": teams[other], "seat": seat,
        "reward": data["rewards"][seat], "opponent_reward": data["rewards"][other],
        "margin": data["rewards"][seat]-data["rewards"][other],
        "same_farmer_fraction": same_fraction("farmer"),
        "same_hands_fraction": same_fraction("hands"),
        "same_market_fraction": same_fraction("market"),
        "first_market": [(steps[t][i].get("action") or {}).get("market") for i in (seat, other) for t in (1,)],
        "day_margin": day_marks, "first_trailing_step": first_t,
        "largest_adverse_swings": swing_rows,
        "our_features": features(steps, seat), "opponent_features": features(steps, other),
        "our_final_tiles": farm_counts(own_farm), "opponent_final_tiles": farm_counts(opponent_farm),
        "our_final_shed": final[seat]["observation"].get("private", {}).get("shed", {}),
    })
(HERE / "LOSS_REPLAY_ANALYSIS.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
groups = {}
for group, predicate in (
    ("similar_actions", lambda r: r["same_farmer_fraction"] >= 0.95 and r["same_hands_fraction"] >= 0.75),
    ("different_actions", lambda r: r["same_farmer_fraction"] < 0.8 or r["same_hands_fraction"] < 0.5),
    ("middle", lambda r: (r["same_farmer_fraction"] < 0.95 or r["same_hands_fraction"] < 0.75)
     and r["same_farmer_fraction"] >= 0.8 and r["same_hands_fraction"] >= 0.5),
):
    v = [r for r in out if predicate(r)]
    groups[group] = {"games": len(v), "wins": sum(r["margin"] > 0 for r in v),
                     "losses": sum(r["margin"] < 0 for r in v),
                     "mean_margin": round(sum(r["margin"] for r in v) / len(v), 1) if v else None,
                     "losses_after_day20_lead": sum(r["margin"] < 0 and r["day_margin"]["19"] > 0 for r in v),
                     "opponents_in_losses": [r["opponent"] for r in v if r["margin"] < 0]}
(HERE / "ACTION_SIMILARITY_SUMMARY.json").write_text(json.dumps(groups, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(groups, ensure_ascii=False, indent=2))
