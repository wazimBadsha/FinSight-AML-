from __future__ import annotations

import argparse
import csv
import json
import random
import signal
import sys
import time
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable

SEED = 20261123
CURRENCIES = ("AED", "USD", "EUR", "INR")
COUNTRIES = ("AE", "SA", "GB", "IN", "US", "DE")
DEFAULT_CHECKPOINT_EVERY = 10_000


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
    # Deterministic synthetic patterns for testing and demonstration only.
    if index % 997 == 0:
        amount, tx_type = 9_800.00, "CASH_DEPOSIT"
    if index % 1499 == 0:
        amount, tx_type = 18_500.00, "TRANSFER_OUT"
    occurred = base + timedelta(minutes=rng.randint(0, 180 * 24 * 60))
    return {
        "transaction_id": f"T{index:09d}",
        "customer_id": customer["customer_id"],
        "occurred_at": occurred.isoformat().replace("+00:00", "Z"),
        "amount": amount,
        "currency": rng.choice(CURRENCIES),
        "transaction_type": tx_type,
        "counterparty_country": rng.choice(COUNTRIES),
        "channel": rng.choice(["BRANCH", "ONLINE", "MOBILE", "ATM"]),
    }


def generate_records(customers: int = 250, transactions: int = 10_000, seed: int = SEED):
    if customers < 1 or transactions < 1:
        raise ValueError("customers and transactions must be positive")
    rng = random.Random(seed)
    customer_rows = generate_customers(customers, rng)
    tx_rows = [
        generate_transaction(i, rng.choice(customer_rows), rng, datetime(2026, 1, 1, tzinfo=timezone.utc))
        for i in range(1, transactions + 1)
    ]
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
            tx = sorted(rows, key=lambda r: r["occurred_at"])[-1]
            alerts.append(_alert(tx, "HIGH_TRANSACTION_COUNT", "LOW", f"Customer has {len(rows)} transactions in the generated observation period."))
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


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict], append: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = append and path.exists() and path.stat().st_size > 0
    with path.open("a" if append else "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def run(output_dir: Path, customers: int = 250, transactions: int = 10_000, seed: int = SEED) -> dict:
    """Backward-compatible in-memory API used by tests and small demonstrations."""
    if customers < 1 or transactions < 1:
        raise ValueError("customers and transactions must be positive")
    customer_rows, tx_rows = generate_records(customers, transactions, seed)
    quality = assess_quality(customer_rows, tx_rows)
    alerts = detect_alerts(tx_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(output_dir / "customers.csv", customer_rows)
    write_csv(output_dir / "transactions.csv", tx_rows)
    write_csv(output_dir / "data_quality_issues.csv", quality)
    write_csv(output_dir / "alerts.csv", alerts)
    summary = _summary(seed, len(customer_rows), len(tx_rows), len(quality), alerts)
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def _summary(seed: int, customers: int, transactions: int, quality_count: int, alerts: list[dict]) -> dict:
    return {
        "seed": seed, "customers": customers, "transactions": transactions,
        "quality_issues": quality_count, "alerts": len(alerts),
        "alert_scenarios": dict(Counter(a["scenario"] for a in alerts)),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "notice": "Synthetic educational data; alerts are heuristics, not evidence of criminal activity.",
    }


def run_streaming(
    output_dir: Path,
    customers: int = 250,
    transactions: int = 10_000,
    seed: int = SEED,
    batch_size: int = 5_000,
    checkpoint_every: int = DEFAULT_CHECKPOINT_EVERY,
    progress: Callable[[dict], None] | None = None,
    should_stop: Callable[[], bool] | None = None,
) -> dict:
    """Generate transaction batches and persist progress; no full transaction list in memory.

    Checkpoints are written atomically at batch boundaries. If the process receives SIGTERM
    or SIGINT it stops after the current batch with status=interrupted; rerun with --resume.
    """
    if customers < 1 or transactions < 1 or batch_size < 1 or checkpoint_every < 1:
        raise ValueError("customers, transactions, batch_size and checkpoint_every must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = output_dir / "checkpoint.json"
    state_path = output_dir / "run_state.json"
    customers_path = output_dir / "customers.csv"
    transactions_path = output_dir / "transactions.csv"
    quality_path = output_dir / "data_quality_issues.csv"
    alerts_path = output_dir / "alerts.csv"

    config = {"customers": customers, "transactions": transactions, "seed": seed}
    state = {"config": config, "last_transaction": 0, "status": "running"}
    if checkpoint_path.exists():
        try:
            existing = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            if existing.get("config") != config:
                raise ValueError("checkpoint configuration differs; use a new output directory or matching parameters")
            state.update(existing)
        except json.JSONDecodeError as exc:
            raise ValueError("checkpoint file is invalid JSON; inspect or remove it before resuming") from exc
    start_index = int(state["last_transaction"])
    if start_index < 0 or start_index > transactions:
        raise ValueError("checkpoint transaction index is out of range")

    rng = random.Random(seed)
    customer_rows = generate_customers(customers, rng)
    # Regenerate the RNG stream deterministically up to the checkpoint. This is intentionally
    # CPU work on resume, but avoids storing the entire input population in memory or relying
    # on implementation-specific random-state serialization.
    if start_index:
        for i in range(1, start_index + 1):
            customer = rng.choice(customer_rows)
            generate_transaction(i, customer, rng, datetime(2026, 1, 1, tzinfo=timezone.utc))

    _write_rows(customers_path, list(customer_rows[0].keys()), customer_rows, append=False)
    if not state.get("initialized"):
        _write_rows(transactions_path, ["transaction_id","customer_id","occurred_at","amount","currency","transaction_type","counterparty_country","channel"], [], append=False)
        _write_rows(quality_path, ["severity","issue","count","record_id"], [], append=False)
        _write_rows(alerts_path, ["alert_id","transaction_id","customer_id","scenario","severity","rationale","status"], [], append=False)
        state["initialized"] = True

    def save_checkpoint(status: str) -> None:
        state["status"] = status
        tmp = checkpoint_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        tmp.replace(checkpoint_path)
        state_path.write_text(json.dumps({
            **state,
            "progress_percent": round(state["last_transaction"] / transactions * 100, 2),
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        }, indent=2), encoding="utf-8")

    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    while state["last_transaction"] < transactions:
        if should_stop and should_stop():
            save_checkpoint("interrupted")
            break
        first = state["last_transaction"] + 1
        last = min(first + batch_size - 1, transactions)
        tx_batch = []
        for i in range(first, last + 1):
            customer = rng.choice(customer_rows)
            tx_batch.append(generate_transaction(i, customer, rng, base))
        _write_rows(transactions_path, list(tx_batch[0].keys()), tx_batch, append=True)
        alert_batch = detect_alerts(tx_batch)
        if alert_batch:
            _write_rows(alerts_path, list(alert_batch[0].keys()), alert_batch, append=True)
        quality_batch = assess_quality(customer_rows, tx_batch)
        if quality_batch:
            _write_rows(quality_path, list(quality_batch[0].keys()), quality_batch, append=True)
        state["last_transaction"] = last
        save_checkpoint("running" if last < transactions else "completed")
        if progress:
            progress({"processed": last, "total": transactions, "percent": round(last / transactions * 100, 2)})
        if should_stop and should_stop():
            save_checkpoint("interrupted")
            break
        # checkpoint_every is a policy interval; each batch is already durably checkpointed.
        if checkpoint_every and last % checkpoint_every < batch_size:
            pass

    state["status"] = "completed" if state["last_transaction"] == transactions else "interrupted"
    save_checkpoint(state["status"])
    return {
        **state,
        "progress_percent": round(state["last_transaction"] / transactions * 100, 2),
        "output_directory": str(output_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic FinSight AML datasets and alerts")
    parser.add_argument("--output", default="data/generated", help="Output directory")
    parser.add_argument("--customers", type=int, default=250)
    parser.add_argument("--transactions", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--stream", action="store_true", help="Use batch processing with checkpoint/resume")
    parser.add_argument("--resume", action="store_true", help="Resume an interrupted streaming run")
    parser.add_argument("--batch-size", type=int, default=5_000)
    parser.add_argument("--checkpoint-every", type=int, default=DEFAULT_CHECKPOINT_EVERY)
    args = parser.parse_args()

    stop_requested = False
    def request_stop(_signum, _frame):
        nonlocal stop_requested
        stop_requested = True
        print("Stop requested; finishing current batch and saving checkpoint...", file=sys.stderr)

    signal.signal(signal.SIGINT, request_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, request_stop)

    if args.stream or args.resume:
        if args.resume and not (Path(args.output) / "checkpoint.json").exists():
            parser.error("--resume requires checkpoint.json in --output")
        result = run_streaming(
            Path(args.output), args.customers, args.transactions, args.seed,
            args.batch_size, args.checkpoint_every,
            progress=lambda p: print(json.dumps(p), flush=True),
            should_stop=lambda: stop_requested,
        )
    else:
        result = run(Path(args.output), args.customers, args.transactions, args.seed)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    main()
