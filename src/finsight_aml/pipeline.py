from __future__ import annotations

import argparse
import csv
import json
import random
import signal
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

SEED = 20261123
CURRENCIES = ("AED", "USD", "EUR", "INR")
COUNTRIES = ("AE", "SA", "GB", "IN", "US", "DE")


def generate_customers(customers: int, rng: random.Random) -> list[dict]:
    if customers < 1:
        raise ValueError("customers must be positive")
    return [{
        "customer_id": f"C{i:07d}",
        "customer_type": "BUSINESS" if i % 5 == 0 else "INDIVIDUAL",
        "risk_band": rng.choices(["LOW", "MEDIUM", "HIGH"], [0.65, 0.27, 0.08])[0],
        "country": rng.choice(COUNTRIES),
        "kyc_complete": 0 if i % 37 == 0 else 1,
        "created_at": "2025-01-01T00:00:00Z",
    } for i in range(1, customers + 1)]


def generate_transaction(index: int, customer: dict, rng: random.Random, base: datetime) -> dict:
    amount = round(rng.lognormvariate(4.0, 1.0), 2)
    tx_type = rng.choice(["CASH_DEPOSIT", "TRANSFER_IN", "TRANSFER_OUT", "CARD_PAYMENT", "CASH_WITHDRAWAL"])
    if index % 997 == 0:
        amount, tx_type = 9_800.00, "CASH_DEPOSIT"
    if index % 1499 == 0:
        amount, tx_type = 18_500.00, "TRANSFER_OUT"
    occurred = base + timedelta(minutes=rng.randint(0, 180 * 24 * 60))
    return {
        "transaction_id": f"T{index:09d}", "customer_id": customer["customer_id"],
        "occurred_at": occurred.isoformat().replace("+00:00", "Z"), "amount": amount,
        "currency": rng.choice(CURRENCIES), "transaction_type": tx_type,
        "counterparty_country": rng.choice(COUNTRIES),
        "channel": rng.choice(["BRANCH", "ONLINE", "MOBILE", "ATM"]),
    }


def generate_records(customers: int = 250, transactions: int = 10_000, seed: int = SEED):
    if customers < 1 or transactions < 1:
        raise ValueError("customers and transactions must be positive")
    rng = random.Random(seed)
    customer_rows = generate_customers(customers, rng)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    tx_rows = [generate_transaction(i, rng.choice(customer_rows), rng, base) for i in range(1, transactions + 1)]
    return customer_rows, tx_rows


def assess_quality(customers: list[dict], transactions: list[dict]) -> list[dict]:
    issues: list[dict] = []
    customer_ids = [r["customer_id"] for r in customers]
    if len(customer_ids) != len(set(customer_ids)):
        issues.append({"severity": "HIGH", "issue": "DUPLICATE_CUSTOMER_ID", "count": len(customer_ids) - len(set(customer_ids))})
    known = set(customer_ids)
    for row in transactions:
        if row["customer_id"] not in known:
            issues.append({"severity": "HIGH", "issue": "ORPHAN_TRANSACTION", "record_id": row["transaction_id"]})
        if row["amount"] <= 0:
            issues.append({"severity": "HIGH", "issue": "NON_POSITIVE_AMOUNT", "record_id": row["transaction_id"]})
        if not row["currency"]:
            issues.append({"severity": "MEDIUM", "issue": "MISSING_CURRENCY", "record_id": row["transaction_id"]})
    for row in customers:
        if not row["country"]:
            issues.append({"severity": "MEDIUM", "issue": "MISSING_CUSTOMER_COUNTRY", "record_id": row["customer_id"]})
    return issues


def detect_alerts(transactions: list[dict]) -> list[dict]:
    alerts: list[dict] = []
    by_customer: dict[str, list[dict]] = {}
    for tx in transactions:
        by_customer.setdefault(tx["customer_id"], []).append(tx)
        if tx["transaction_type"] == "CASH_DEPOSIT" and 9_000 <= tx["amount"] < 10_000:
            alerts.append(_alert(tx, "CASH_DEPOSIT_NEAR_THRESHOLD", "MEDIUM", "Cash deposit falls within an illustrative review band."))
        if tx["transaction_type"] == "TRANSFER_OUT" and tx["amount"] >= 15_000:
            alerts.append(_alert(tx, "HIGH_VALUE_TRANSFER", "MEDIUM", "Transfer meets an illustrative high-value review threshold."))
    for _, rows in by_customer.items():
        if len(rows) >= 45:
            tx = max(rows, key=lambda r: r["occurred_at"])
            alerts.append(_alert(tx, "HIGH_TRANSACTION_COUNT", "LOW", f"Customer has {len(rows)} transactions in this observation window."))
    return alerts


def _alert(tx: dict, scenario: str, severity: str, rationale: str) -> dict:
    return {"alert_id": f"A-{tx['transaction_id']}-{scenario}", "transaction_id": tx["transaction_id"],
            "customer_id": tx["customer_id"], "scenario": scenario, "severity": severity,
            "rationale": rationale, "status": "OPEN"}


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _append_rows(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def run(output_dir: Path, customers: int = 250, transactions: int = 10_000, seed: int = SEED) -> dict:
    if customers < 1 or transactions < 1:
        raise ValueError("customers and transactions must be positive")
    customer_rows, tx_rows = generate_records(customers, transactions, seed)
    quality, alerts = assess_quality(customer_rows, tx_rows), detect_alerts(tx_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "customers.csv", customer_rows)
    write_csv(output_dir / "transactions.csv", tx_rows)
    write_csv(output_dir / "data_quality_issues.csv", quality)
    write_csv(output_dir / "alerts.csv", alerts)
    summary = _summary(seed, len(customer_rows), len(tx_rows), len(quality), alerts)
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _summary(seed: int, customers: int, transactions: int, quality_count: int, alerts: list[dict]) -> dict:
    return {"seed": seed, "customers": customers, "transactions": transactions, "quality_issues": quality_count,
            "alerts": len(alerts), "alert_scenarios": dict(Counter(a["scenario"] for a in alerts)),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "notice": "Synthetic educational data; alerts are heuristics, not evidence of criminal activity."}


def run_streaming(output_dir: Path, customers: int = 250, transactions: int = 10_000, seed: int = SEED,
                  batch_size: int = 5_000, progress: Callable[[dict], None] | None = None,
                  should_stop: Callable[[], bool] | None = None) -> dict:
    if min(customers, transactions, batch_size) < 1:
        raise ValueError("customers, transactions and batch_size must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint = output_dir / "checkpoint.json"
    state_file = output_dir / "run_state.json"
    config = {"customers": customers, "transactions": transactions, "seed": seed, "batch_size": batch_size}
    state = {"config": config, "last_transaction": 0, "status": "running"}
    if checkpoint.exists():
        saved = json.loads(checkpoint.read_text(encoding="utf-8"))
        if saved.get("config") != config:
            raise ValueError("checkpoint configuration differs; use a new output directory or matching parameters")
        state.update(saved)

    customer_rng = random.Random(seed)
    customer_rows = generate_customers(customers, customer_rng)
    # Rebuild the RNG stream exactly to the last committed transaction.
    rng = random.Random(seed)
    _ = generate_customers(customers, rng)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    last = int(state["last_transaction"])
    for i in range(1, last + 1):
        generate_transaction(i, rng.choice(customer_rows), rng, base)

    def atomic_json(path: Path, payload: dict) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(path)

    customers_path = output_dir / "customers.csv"
    if not customers_path.exists():
        write_csv(customers_path, customer_rows)
    fieldnames = ["transaction_id", "customer_id", "occurred_at", "amount", "currency", "transaction_type", "counterparty_country", "channel"]
    for name, fields in [
        ("transactions.csv", fieldnames),
        ("alerts.csv", ["alert_id", "transaction_id", "customer_id", "scenario", "severity", "rationale", "status"]),
        ("data_quality_issues.csv", ["severity", "issue", "count", "record_id"]),
    ]:
        target = output_dir / name
        if not target.exists():
            _append_rows(target, fields, [])

    while last < transactions:
        if should_stop and should_stop():
            break
        first, end = last + 1, min(last + batch_size, transactions)
        batch = []
        for idx in range(first, end + 1):
            batch.append(generate_transaction(idx, rng.choice(customer_rows), rng, base))
        # Stage outputs first; checkpoint only advances after appends complete.
        alert_rows = detect_alerts(batch)
        quality_rows = assess_quality(customer_rows, batch)
        _append_rows(output_dir / "transactions.csv", fieldnames, batch)
        if alert_rows:
            _append_rows(output_dir / "alerts.csv", list(alert_rows[0]), alert_rows)
        if quality_rows:
            _append_rows(output_dir / "data_quality_issues.csv", list(quality_rows[0]), quality_rows)
        last = end
        state.update({"last_transaction": last, "status": "running"})
        atomic_json(checkpoint, state)
        atomic_json(state_file, {**state, "progress_percent": round(last / transactions * 100, 2),
                                 "updated_at_utc": datetime.now(timezone.utc).isoformat()})
        if progress:
            progress({"processed": last, "total": transactions, "percent": round(last / transactions * 100, 2)})

    state.update({"last_transaction": last, "status": "completed" if last == transactions else "interrupted"})
    atomic_json(checkpoint, state)
    result = {**state, "progress_percent": round(last / transactions * 100, 2), "output_directory": str(output_dir)}
    atomic_json(state_file, {**result, "updated_at_utc": datetime.now(timezone.utc).isoformat()})
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="FinSight AML synthetic analytics pipeline")
    parser.add_argument("--output", default="data/generated")
    parser.add_argument("--customers", type=int, default=250)
    parser.add_argument("--transactions", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--stream", action="store_true", help="Use bounded batches and durable checkpoints")
    parser.add_argument("--resume", action="store_true", help="Resume streaming from checkpoint.json")
    parser.add_argument("--batch-size", type=int, default=5_000)
    args = parser.parse_args()
    stop = {"requested": False}

    def handle_stop(_signum, _frame):
        stop["requested"] = True
        print("Stop requested; finish current batch and checkpoint.", file=sys.stderr, flush=True)

    signal.signal(signal.SIGINT, handle_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handle_stop)
    if args.stream or args.resume:
        result = run_streaming(Path(args.output), args.customers, args.transactions, args.seed,
                               args.batch_size, progress=lambda p: print(json.dumps(p), flush=True),
                               should_stop=lambda: stop["requested"])
        print(json.dumps(result, indent=2), flush=True)
        if result["status"] != "completed":
            raise SystemExit(2)
    else:
        print(json.dumps(run(Path(args.output), args.customers, args.transactions, args.seed), indent=2), flush=True)


if __name__ == "__main__":
    main()
