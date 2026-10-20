"""SXF / AI — original offline replay experiment.
120 unique logical tasks, 3 deliveries each, one simulated process restart.
No model calls, cloud services or remote side effects. Stdlib + SQLite only.

Run: python deployment-replay-lab.py
"""
from __future__ import annotations
import json
import sqlite3
import tempfile
from pathlib import Path

TASKS = 120
PASSES = 3

def simulate(mode: str, database: Path) -> dict:
    seen_in_memory: set[str] = set()
    db = sqlite3.connect(database)
    db.execute("CREATE TABLE IF NOT EXISTS ledger (operation_key TEXT PRIMARY KEY)")
    db.execute("CREATE TABLE IF NOT EXISTS effects (operation_key TEXT NOT NULL)")
    db.commit()
    suppressed = 0
    for phase in range(PASSES):
        if phase == 2:
            db.close()
            seen_in_memory.clear()
            db = sqlite3.connect(database)
        for n in range(TASKS):
            key = f"task-{n:03d}:send-confirmation"
            if mode == "naive":
                db.execute("INSERT INTO effects VALUES (?)", (key,))
                db.commit()
            elif mode == "ram":
                if key in seen_in_memory:
                    suppressed += 1
                    continue
                seen_in_memory.add(key)
                db.execute("INSERT INTO effects VALUES (?)", (key,))
                db.commit()
            elif mode == "durable":
                # Atomic for LOCAL SQL writes only.
                # External tools require target-side idempotency and reconciliation.
                with db:
                    record = db.execute(
                        "INSERT OR IGNORE INTO ledger (operation_key) VALUES (?)", (key,)
                    )
                    if record.rowcount:
                        db.execute("INSERT INTO effects VALUES (?)", (key,))
                    else:
                        suppressed += 1
            else:
                raise ValueError(mode)
    effects = db.execute("SELECT COUNT(*) FROM effects").fetchone()[0]
    distinct = db.execute("SELECT COUNT(DISTINCT operation_key) FROM effects").fetchone()[0]
    db.close()
    return {
        "strategy": mode, "deliveries": TASKS * PASSES,
        "unique_tasks": TASKS, "recorded_effects": effects,
        "duplicate_effects": effects - distinct,
        "suppressed_deliveries": suppressed, "simulated_restarts": 1
    }

def main():
    with tempfile.TemporaryDirectory(prefix="sxf-deploy-") as tmp:
        results = [
            simulate(mode, Path(tmp) / f"{mode}.db")
            for mode in ("naive", "ram", "durable")
        ]
    expected = [(360, 240, 0), (240, 120, 120), (120, 0, 240)]
    for result, value in zip(results, expected):
        observed = (
            result["recorded_effects"],
            result["duplicate_effects"],
            result["suppressed_deliveries"]
        )
        assert observed == value, (observed, value)
    print(json.dumps({"method": "offline deterministic replay", "results": results}, indent=2))

if __name__ == "__main__":
    main()
