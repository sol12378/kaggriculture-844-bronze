"""Explain the public action tapes that survived the tournament screen."""
import json
import runpy
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
names = ("rank95_basic", "rank88_c_full", "rank97_basic", "rank32_screen")
report = {}
for name in names:
    route = runpy.run_path(str(HERE / "candidates" / name / "main.py"))["_DISTILLED_ROUTE"]
    farmers, hands, market, sell_products = Counter(), Counter(), Counter(), Counter()
    for action in route:
        farmer = action.get("farmer") or []
        if farmer: farmers[str(farmer[0])] += 1
        for hand in action.get("hands") or []:
            if hand: hands[str(hand[0])] += 1
        for order in action.get("market") or []:
            if order:
                market[str(order[0])] += 1
                if order[0] == "SELL" and len(order) >= 2: sell_products[str(order[1])] += 1
    provenance = json.loads((HERE / "candidates" / name / "PROVENANCE.json").read_text(encoding="utf-8"))
    report[name] = {"origin_rank": provenance["rank"], "origin_episode": provenance["episode_id"],
                    "farmer_commands": dict(farmers), "hand_commands": dict(hands),
                    "market_orders": dict(market), "sell_product_orders": dict(sell_products)}
(HERE / "FINALIST_ROUTE_CHARACTERISTICS.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
