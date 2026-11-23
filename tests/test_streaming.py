from finsight_aml.pipeline import run_streaming


def test_streaming_completes_and_writes_checkpoint(tmp_path):
    result = run_streaming(tmp_path, customers=20, transactions=125, seed=9, batch_size=25)
    assert result["status"] == "completed"
    assert result["last_transaction"] == 125
    assert (tmp_path / "transactions.csv").exists()
    assert (tmp_path / "checkpoint.json").exists()
    assert (tmp_path / "run_state.json").exists()


def test_streaming_can_resume_after_interruption(tmp_path):
    calls = {"count": 0}

    def stop_after_one_batch():
        calls["count"] += 1
        return calls["count"] >= 2

    first = run_streaming(tmp_path, customers=20, transactions=100, seed=9, batch_size=25,
                          should_stop=stop_after_one_batch)
    assert first["status"] == "interrupted"
    assert first["last_transaction"] == 25

    second = run_streaming(tmp_path, customers=20, transactions=100, seed=9, batch_size=25)
    assert second["status"] == "completed"
    assert second["last_transaction"] == 100


def test_resume_rejects_changed_configuration(tmp_path):
    run_streaming(tmp_path, customers=10, transactions=20, seed=1, batch_size=10,
                  should_stop=lambda: True)
    try:
        run_streaming(tmp_path, customers=11, transactions=20, seed=1, batch_size=10)
    except ValueError as exc:
        assert "configuration differs" in str(exc)
    else:
        raise AssertionError("expected checkpoint configuration mismatch")
