"""Summarize intended actions in the frozen top-20 public replay tapes."""

from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAPES = ROOT / "top20_replay_distill_20260930" / "tapes"
rows = defaultdict(list)
for path in sorted(TAPES.glob("rank*_episode*_seat*.json.gz")):
    rank = int(path.name[4:6])
    actions = json.load(gzip.open(path, "rt", encoding="utf-8"))
    sold = Counter()
    buys = Counter()
    workers = Counter()
    open_orders = Counter()
    for step, action in enumerate(actions):
        for order in action.get("market", []):
            if not order:
                continue
            if order[0] == "SELL" and len(order) >= 3:
                sold[order[1]] += int(order[2])
            elif order[0] in ("BUY_ANIMAL", "BUY_PRODUCT", "BUY_SEED") and len(order) >= 3:
                buys[(order[0], order[1])] += int(order[2])
            if step < 24:
                open_orders[order[0]] += 1
        commands = [action.get("farmer"), *(action.get("hands") or [])]
        for command in commands:
            if command:
                workers[command[0]] += 1
    opening = tuple(tuple(order) for order in actions[0].get("market", [])) if actions else ()
    rows[rank].append((sold, buys, workers, open_orders, opening))

out = []
for rank, records in sorted(rows.items()):
    n = len(records)
    total_sold = sum((record[0] for record in records), Counter())
    total_buys = sum((record[1] for record in records), Counter())
    total_workers = sum((record[2] for record in records), Counter())
    total_open = sum((record[3] for record in records), Counter())
    openings = Counter(str(record[4]) for record in records)
    out.append({
        "rank": rank,
        "tapes": n,
        "mean_intended_sells_per_game": {k: round(v / n, 1) for k, v in total_sold.most_common()},
        "mean_intended_buys_per_game": {f"{k[0]}:{k[1]}": round(v / n, 1) for k, v in total_buys.most_common()},
        "mean_worker_actions_per_game": {k: round(v / n, 1) for k, v in total_workers.most_common()},
        "mean_opening_market_order_counts": {k: round(v / n, 1) for k, v in total_open.most_common()},
        "common_step0_market": openings.most_common(3),
    })
(Path(__file__).resolve().parent / "META_TAPE_SUMMARY.json").write_text(
    json.dumps({"note": "Orders are issued actions, not proven fulfilled executions.",
                "tapes": sum(len(v) for v in rows.values()), "rows": out}, indent=2), encoding="utf-8")
for row in out:
    print(row["rank"], "tapes", row["tapes"],
          "top sells", list(row["mean_intended_sells_per_game"].items())[:5],
          "animal buys", [(k, v) for k, v in row["mean_intended_buys_per_game"].items() if k.startswith("BUY_ANIMAL")],
          "step0", row["common_step0_market"][:1],
          flush=True)
