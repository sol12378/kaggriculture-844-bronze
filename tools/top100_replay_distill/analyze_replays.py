"""Extract auditable behavioral and economic summaries from top-100 replays."""

import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).resolve().parent
MANIFEST = json.loads((HERE / "MANIFEST.json").read_text(encoding="utf-8"))
ROWS = HERE / "TRAJECTORIES.jsonl"
SNAPSHOTS = (0, 23, 47, 119, 239, 359, 479, 599, 647, 695, 718)
PHASES = ((0, 48, "opening"), (48, 240, "build"), (240, 576, "mid"), (576, 696, "late"), (696, 719, "terminal"))


def phase(step):
    for lo, hi, name in PHASES:
        if lo <= step < hi:
            return name
    raise ValueError(step)


def snapshot(obs, seat):
    farm = obs["farms"][seat]
    tiles = Counter()
    for line in farm["tiles"]:
        for tile in line:
            if isinstance(tile, dict):
                if tile.get("kind") == "PLANT":
                    tiles[f"plant:{tile.get('crop')}"] += 1
                elif tile.get("kind") in ("PASTURE", "COOP"):
                    tiles[f"animal:{tile.get('animal')}"] += 1
                else:
                    tiles[f"other:{tile.get('kind')}"] += 1
    shed = obs["private"].get("shed", {})
    prices = obs["market"]["prices"]
    stock_value = sum(qty * prices.get(item, 0) for item, qty in shed.items())
    return {"cash": farm["money"], "hands": len(farm["hands"]),
            "quadrants": len(farm["unlocked_quadrants"]), "tiles": dict(tiles),
            "shed": shed, "shed_mark_value": round(stock_value, 2)}


def summarize(replay, eid, target):
    sid = target["submission_id"]
    target_seat = next((i for i, agent in enumerate(MANIFEST["episodes"][eid]["agents"])
                        if agent.get("submissionId") == sid and agent.get("teamId") == target["team_id"]), None)
    if target_seat is None:
        raise ValueError(f"episode {eid} absent rank {target['rank']} submission {sid}")
    seat = target_seat
    first_obs = replay["steps"][0][seat]["observation"]
    market = defaultdict(Counter)
    market_item = defaultdict(Counter)
    market_active = Counter()
    workers = defaultdict(Counter)
    order_lengths = Counter()
    opening_orders = []
    opening_farmer = []
    opening_hands = []
    snaps = {str(0): snapshot(first_obs, seat)}
    for step in range(719):
        action = replay["steps"][step + 1][seat].get("action") or {}
        if not isinstance(action, dict):
            action = {}
        ph = phase(step)
        orders = action.get("market") or []
        order_lengths[str(len(orders))] += 1
        if orders:
            market_active[ph] += 1
        for order in orders:
            if not isinstance(order, list) or not order:
                continue
            op = str(order[0])
            market[ph][op] += 1
            item = str(order[1]) if len(order) > 1 else ""
            qty = order[2] if len(order) > 2 and isinstance(order[2], (int, float)) else 0
            market_item[ph][f"{op}:{item}"] += qty
            if step < 48:
                opening_orders.append([step, *order])
        local = [action.get("farmer"), *(action.get("hands") or [])]
        for i, command in enumerate(local):
            if isinstance(command, list) and command:
                workers[ph][str(command[0])] += 1
                if step < 24:
                    (opening_farmer if i == 0 else opening_hands).append([step, i, *command])
        if step in SNAPSHOTS and step != 0:
            snaps[str(step)] = snapshot(replay["steps"][step][seat]["observation"], seat)
    # Last recorded state is after applying action at step 718.
    final_obs = replay["steps"][-1][seat]["observation"]
    final_farm = final_obs["farms"][seat]
    return {"rank": target["rank"], "team_id": target["team_id"], "team_name": target["team_name"],
            "submission_id": sid, "episode_id": eid, "split": MANIFEST["episodes"][eid]["split"],
            "seat": seat, "opponent": replay["info"]["TeamNames"][1 - seat],
            "reward": replay["rewards"][seat], "opponent_reward": replay["rewards"][1 - seat],
            "status": replay["statuses"][seat], "market_orders_by_phase": {k: dict(v) for k, v in market.items()},
            "market_quantities_by_phase": {k: dict(v) for k, v in market_item.items()},
            "market_active_steps_by_phase": dict(market_active), "order_slot_counts": dict(order_lengths),
            "worker_actions_by_phase": {k: dict(v) for k, v in workers.items()},
            "opening_orders": opening_orders, "opening_farmer": opening_farmer, "opening_hands": opening_hands,
            "snapshots": snaps, "terminal_cash": final_farm["money"],
            "terminal_shed": final_obs["private"].get("shed", {})}


done = set()
if ROWS.exists():
    for line in ROWS.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        done.add((row["episode_id"], row["rank"]))

count = 0
for eid, episode in MANIFEST["episodes"].items():
    path = HERE / "replays" / f"episode-{eid}-replay.json.gz"
    if not path.exists():
        continue
    ranks = episode["source_ranks"]
    if all((eid, rank) in done for rank in ranks):
        continue
    with gzip.open(path, "rb") as handle:
        replay = json.load(handle)
    assert str(replay["info"]["EpisodeId"]) == eid
    for rank in ranks:
        if (eid, rank) in done:
            continue
        row = summarize(replay, eid, {"rank": rank, **MANIFEST["ranks"][str(rank)]})
        with ROWS.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        done.add((eid, rank))
        count += 1
    if count and count % 50 == 0:
        print(f"summarized {count} trajectories this run", flush=True)
print(f"total trajectory summaries {len(done)}; new {count}")
