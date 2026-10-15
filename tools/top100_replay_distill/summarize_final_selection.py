"""Rank distinct finalist strategies from the official seat-balanced tournament."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
data = json.loads((HERE / "OFFICIAL_FINAL_LEAGUE_36330001_24.json").read_text(encoding="utf-8"))
assert sum(map(len, data["pairs"].values())) == 1728, "official tournament incomplete"
assert data["errors"] == 0
challenger = json.loads((HERE / "OFFICIAL_RANK95_FRONT_CHALLENGER_36330001_24.json").read_text(encoding="utf-8"))
assert len(challenger["rows"]) == 432, "rank95 challenger tournament incomplete"
assert all(r["candidate_status"] == "DONE" and r["baseline_status"] == "DONE"
           for r in challenger["rows"])

# This list retains one representative of the nearly identical meta-front pair;
# the duplicate remains in the raw tournament and is compared separately.
PEERS = ("rank95_front97", "environment_meta_front_97", "rank32_plus8_front97",
         "rank32_plus8", "rank88_c_full", "rank97_plus4")
CONTROLS = ("submitted", "second_meta")


def duel(a, b):
    if "rank95_front97" in (a, b):
        other = b if a == "rank95_front97" else a
        rows = [r for r in challenger["rows"] if r["opponent"] == other]
        assert len(rows) == 48
        sign = 1 if a == "rank95_front97" else -1
        margins = [sign * (r["candidate_reward"] - r["baseline_reward"]) for r in rows]
        wins = sum(m > 0 for m in margins)
        losses = sum(m < 0 for m in margins)
        ties = 48 - wins - losses
        mean_margin = round(sum(margins) / 48, 2)
    else:
        row = data["matrix"][a][b]
        wins, losses, ties, mean_margin = row["wins"], row["losses"], row["ties"], row["mean_margin"]
    return {"wins": wins, "losses": losses, "ties": ties,
            "halfwin_rate": round((wins + .5 * ties) / 48, 4), "mean_margin": mean_margin}


ranking = []
for agent in PEERS:
    duels = {other: duel(agent, other) for other in PEERS if other != agent}
    wins = sum(v["wins"] for v in duels.values())
    ties = sum(v["ties"] for v in duels.values())
    games = 48 * len(duels)
    ranking.append({"agent": agent, "peer_halfwin_rate": round((wins + .5 * ties) / games, 4),
                    "peer_wins": wins, "peer_ties": ties, "peer_games": games,
                    "mean_margin": round(sum(v["mean_margin"] for v in duels.values()) / len(duels), 2),
                    "pair_wins": sum(v["wins"] > v["losses"] for v in duels.values()),
                    "pair_losses": sum(v["wins"] < v["losses"] for v in duels.values()),
                    "worst_duel_halfwin": min(v["halfwin_rate"] for v in duels.values()),
                    "duels": duels, "controls": {c: duel(agent, c) for c in CONTROLS}})
ranking.sort(key=lambda r: (r["peer_halfwin_rate"], r["pair_wins"],
                            r["worst_duel_halfwin"], r["mean_margin"]), reverse=True)
out = {"engine": data["engine"], "seeds": data["seeds"], "matches": 2160,
       "errors": data["errors"], "distinct_peers": PEERS,
       "excluded_near_duplicates": ["environment_meta_v2_front97", "rank95_basic"],
       "near_duplicate_duel": duel("environment_meta_v2_front97", "environment_meta_front_97"),
       "rank95_ablation_duel": duel("rank95_front97", "rank95_basic"),
       "ranking": ranking, "winner": ranking[0]["agent"]}
(HERE / "FINAL_SELECTION.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps({"winner": out["winner"], "ranking": [{k:v for k,v in r.items()
        if k in ("agent", "peer_halfwin_rate", "peer_wins", "peer_ties", "peer_games",
                 "mean_margin", "pair_wins", "pair_losses", "worst_duel_halfwin")}
       for r in ranking], "near_duplicate_duel": out["near_duplicate_duel"]}, indent=2))
