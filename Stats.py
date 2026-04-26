import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATS_FILE = os.path.join(BASE_DIR, "stats.json")

DEFAULT = {
    "wins": 0, "losses": 0, "best_moves": None,
    "best_time": None, "move_history": [],
}

def load():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r") as f:
                data = json.load(f)
            for k, v in DEFAULT.items():
                data.setdefault(k, v)
            return data
        except (json.JSONDecodeError, IOError):
            return dict(DEFAULT)
    return dict(DEFAULT)

def save(stats):
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=2)

def record_win(stats, moves_taken, elapsed_seconds):
    stats["wins"] += 1
    stats["move_history"].append(moves_taken)
    stats["move_history"] = stats["move_history"][-50:]
    if stats["best_moves"] is None or moves_taken < stats["best_moves"]:
        stats["best_moves"] = moves_taken
    if stats["best_time"] is None or elapsed_seconds < stats["best_time"]:
        stats["best_time"] = elapsed_seconds
    save(stats)

def record_loss(stats):
    stats["losses"] += 1
    save(stats)

def win_ratio(stats):
    total = stats["wins"] + stats["losses"]
    return stats["wins"] / total if total > 0 else 0.0

def average_moves(stats):
    h = stats["move_history"]
    return sum(h) / len(h) if h else None

def format_time(seconds):
    if seconds is None: return "—"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s" if m else f"{s}s"

def summary(stats):
    total = stats["wins"] + stats["losses"]
    ratio = f"{win_ratio(stats):.0%}" if total else "—"
    avg = average_moves(stats)
    return (
        f"Wins: {stats['wins']}  Losses: {stats['losses']}  "
        f"Win rate: {ratio}\n"
        f"Best moves: {stats['best_moves'] or '—'}  "
        f"Best time: {format_time(stats['best_time'])}  "
        f"Avg moves: {f'{avg:.1f}' if avg else '—'}"
    )
