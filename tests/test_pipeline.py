from finsight_aml.pipeline import assess_quality, detect_alerts, generate_records, run


def test_generator_is_deterministic():
    c1, t1 = generate_records(10, 100, 42)
    c2, t2 = generate_records(10, 100, 42)
    assert c1 == c2
    assert t1 == t2


def test_generator_rejects_invalid_sizes():
    try:
        generate_records(0, 10)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")


def test_quality_flags_orphan_and_invalid_amount():
    customers = [{"customer_id": "C1", "country": "AE"}]
    transactions = [
        {"transaction_id": "T1", "customer_id": "MISSING", "amount": 0, "currency": "AED"}
    ]
    issues = assess_quality(customers, transactions)
    assert {i["issue"] for i in issues} >= {"ORPHAN_TRANSACTION", "NON_POSITIVE_AMOUNT"}


def test_alert_rules_return_explainable_alerts():
    txs = [{"transaction_id": "T1", "customer_id": "C1", "transaction_type": "CASH_DEPOSIT",
            "amount": 9800, "occurred_at": "2026-01-01T00:00:00Z"}]
    alerts = detect_alerts(txs)
    assert len(alerts) == 1
    assert alerts[0]["scenario"] == "CASH_DEPOSIT_NEAR_THRESHOLD"
    assert alerts[0]["rationale"]


def test_run_writes_expected_outputs(tmp_path):
    summary = run(tmp_path, customers=8, transactions=40, seed=7)
    assert summary["customers"] == 8
    assert summary["transactions"] == 40
    for name in ("customers.csv", "transactions.csv", "alerts.csv", "data_quality_issues.csv", "run_summary.json"):
        assert (tmp_path / name).is_file()
