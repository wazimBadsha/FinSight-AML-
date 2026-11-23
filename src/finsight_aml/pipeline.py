from __future__ import annotations

import argparse
import csv
import json
import random
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

SEED = 20261123
CURRENCIES = ("AED", "USD", "EUR", "INR")
COUNTRIES = ("AE", "SA", "GB", "IN", "US", "DE")


def generate_records(customers: int = 250, transactions: int = 10_000, seed: int = SEED):
    if customers < 1 or transactions < 1:
        raise ValueError("customers and transactions must be positive")
    rng = random.Random(seed)
    customer_rows = []
    for i in range(1, customers + 1):
        customer_rows.append({
            "customer_id": f"C{i:05d}",
            "customer_type": "BUSINESS" if i % 5 == 0 else "INDIVIDUAL",
            "risk_band": rng.choices(["LOW", "MEDIUM", "HIGH"], [0.65, 0.27, 0.08])[0],
            "country": rng.choice(COUNTRIES),
            "kyc_complete": 0 if i % 37 == 0 else 1,
            "created_at": "2025-01-01T00:00:00Z",
        })
    tx_rows = []
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    for i in range(1, transactions + 1):
        customer = rng.choice(customer_rows)
        amount = round(rng.lognormvariate(4.0, 1.0), 2)
        tx_type = rng.choice(["CASH_DEPOSIT", "TRANSFER_IN", "TRANSFER_OUT", "CARD_PAYMENT", "CASH_WITHDRAWAL"])
        # Deterministic synthetic patterns for testing and demonstration only.
        if i % 997 == 0:
            amount = 9_800.00
            tx_type = "CASH_DEPOSIT"
        if i % 1499 == 0:
            amount = 18_500.00
            tx_type = "TRANSFER_OUT"
        occurred = base + timedelta(minutes=rng.randint(0, 180 * 24 * 60))
        tx_rows.append({
            "transaction_id": f"T{i:07d}",
            "customer_id": customer["customer_id"],
            "occurred_at": occurred.isoformat().replace("+00:00", "Z"),
            "amount": amount,
            "currency": rng.choice(CURRENCIES),
            "transaction_type": tx_type,
            "counterparty_country": rng.choice(COUNTRIES),
            "channel": rng.choice(["BRANCH", "ONLINE", "MOBILE", "ATM"]),
        })
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
            issues.append({"severity": "MEDIUM", "issue": "MISSING_CURRENCY", "record_id": row["transaction_id"])
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
    for customer_id, rows in by_customer.items():
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


def run(output_dir: Path, customers: int = 250, transactions: int = 10_000, seed: int = SEED) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    customer_rows, tx_rows = generate_records(customers, transactions, seed)
    quality = assess_quality(customer_rows, tx_rows)
    alerts = detect_alerts(tx_rows)
    write_csv(output_dir / "customers.csv", customer_rows)
    write_csv(output_dir / "transactions.csv", tx_rows)
    write_csv(output_dir / "data_quality_issues.csv", quality)
    write_csv(output_dir / "alerts.csv", alerts)
    summary = {
        "seed": seed, "customers": len(customer_rows), "transactions": len(tx_rows),
        "quality_issues": len(quality), "alerts": len(alerts),
        "alert_scenarios": dict(Counter(a["scenario"] for a in alerts)),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "notice": "Synthetic educational data; alerts are heuristics, not evidence of criminal activity.",
    }
    (output_dir / "run_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic FinSight AML datasets and alerts")
    parser.add_argument("--output", default="data/generated", help="Output directory")
    parser.add_argument("--customers", type=int, default=250)
    parser.add_argument("--transactions", type=int, default=10_000)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()
    print(json.dumps(run(Path(args.output), args.customers, args.transactions, args.seed), indent=2))


if __name__ == "__main__":
    main()
