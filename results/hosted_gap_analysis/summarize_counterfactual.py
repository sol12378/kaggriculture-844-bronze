"""Create an auditable aggregate of local fixed-action counterfactuals."""
import json
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).resolve().parent
def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))

hosted = {r["episode_id"]: r for r in read("HOSTED_EPISODES.json")}
rows = read("TAPE_COUNTERFACTUAL_LOSSES.json") + read("TAPE_COUNTERFACTUAL_WINS.json") + read("TAPE_COUNTERFACTUAL_NEW.json")
first = {r["episode_id"]: r for r in rows if r["candidate"] == "first"}
second = {r["episode_id"]: r for r in rows if r["candidate"] == "second_h5"}
ids = sorted(second)
assert len(ids) == len(set(ids)) == 57
assert all(first[e]["reward"] == first[e]["recorded_reward"] and
           first[e]["opponent_reward"] == first[e]["recorded_opponent_reward"] for e in first)
delta = [(second[e]["reward"] - second[e]["opponent_reward"]) - hosted[e]["margin"] for e in ids]
report = {
    "hosted_snapshot_games": len(ids),
    "hosted_wins": sum(hosted[e]["outcome"] == "win" for e in ids),
    "hosted_losses": sum(hosted[e]["outcome"] == "loss" for e in ids),
    "exact_first_reproductions": len(first),
    "exact_first_reproduction_failures": 0,
    "second_h5_wins_fixed_tape": sum(second[e]["reward"] > second[e]["opponent_reward"] for e in ids),
    "second_h5_losses_fixed_tape": sum(second[e]["reward"] < second[e]["opponent_reward"] for e in ids),
    "loss_to_win": [e for e in ids if hosted[e]["outcome"] == "loss" and
                    second[e]["reward"] > second[e]["opponent_reward"]],
    "win_to_loss": [e for e in ids if hosted[e]["outcome"] == "win" and
                    second[e]["reward"] < second[e]["opponent_reward"]],
    "mean_margin_delta": mean(delta),
    "median_margin_delta": median(delta),
    "positive_margin_delta_games": sum(d > 0 for d in delta),
    "negative_margin_delta_games": sum(d < 0 for d in delta),
    "limitation": "Opponent actions are fixed to the recorded tape and do not react to the candidate's changed state.",
    "submission_performed": False,
}
(HERE / "COUNTERFACTUAL_SUMMARY.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
