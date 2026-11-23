# FinSight AML — Engineering Handoff

**Version:** 0.2.0  
**Delivery:** Synthetic-data analytics portfolio demonstrator  
**Implementation scope:** Resumable batch/streaming CLI and CI smoke tests

## 1. Root cause
The initial CLI generated all transactions into an in-memory list, then analysed and exported the entire collection at the end. This is a finite batch process, not a durable background worker. Large workloads therefore consume memory proportional to total transaction count and provide no persisted progress if terminated.

GitHub Actions is also a finite CI execution environment, not a permanent background host. It terminates jobs at completion or when platform/job limits are reached. A repository cannot create an indefinitely running process simply by pushing code.

The README disclaimer about synthetic data and illustrative rules is a responsible-use notice. It does not cause process termination or control runtime behavior.

## 2. Changes in this repair
- Preserved the original `run()` batch API for existing callers/tests.
- Added a streaming CLI mode (`--stream`) that generates and persists bounded transaction batches.
- Added atomic checkpoint and run-state JSON writes at batch boundaries.
- Added progress JSON output to stdout.
- Added SIGINT/SIGTERM handling that finishes the current batch and persists an interrupted state.
- Added `--resume` support with strict run-configuration matching.
- Added streaming completion, interruption/resume and mismatch tests.
- Added GitHub Actions smoke coverage for the streaming path.
- Documented why GitHub Actions is not a permanent background process host and included a systemd oneshot example for managed Linux execution.

## 3. Usage
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest -q

# Small in-memory batch mode (backward compatible)
python -m finsight_aml.pipeline --customers 250 --transactions 10000 --output data/generated

# Streaming mode
python -m finsight_aml.pipeline --stream --customers 250 --transactions 1000000 --batch-size 5000 --output data/long-run

# Resume after Ctrl+C / SIGTERM
python -m finsight_aml.pipeline --stream --resume --customers 250 --transactions 1000000 --batch-size 5000 --output data/long-run
```

## 4. Runtime contract
- Batch mode remains finite and uses memory proportional to input data.
- Streaming mode keeps each transaction batch bounded in memory; customer profiles and alert aggregation remain in memory.
- Checkpoints are written after each batch, so a crash can lose at most the currently written batch if termination occurs during file output. See risks below.
- Resume is deterministic when run parameters match; it replays the seeded random stream to the checkpoint. Long resumes take longer as the checkpoint index grows.
- The process does not daemonize itself. Use systemd, Supervisor or a container orchestrator for managed execution.
- GitHub Actions validates behavior but must not be used as a persistent 24/7 worker.

## 5. Verification
CI will verify:
- Unit tests, including stream completion and interruption/resume.
- Batch pipeline smoke test.
- Streaming pipeline smoke test.
- Final checkpoint status and total transaction count.

Do not mark the repair verified until the workflow for the repair commit is completed successfully.

## 6. Known limitations and future hardening
- Output CSVs are append-based and checkpointing is batch-boundary based. For robust recovery from partial writes, implement transaction-batch staging files and atomic rename/manifest commit before advancing the checkpoint.
- Resume replays the RNG stream to reconstruct state, so resume time is O(checkpoint index); a future version should persist RNG state or deterministic per-index generation.
- Current alert detection evaluates each batch independently; the transaction-count scenario is therefore batch-scoped in streaming mode, not equivalent to full-run aggregation. A production-grade design should maintain durable per-customer aggregate state or process a second aggregate pass.
- Customer population remains in memory; a database-backed customer dimension is the next scaling step.
- PostgreSQL DDL and query assets are not integrated or execution-verified.
- Power BI report/`.pbix` is not included or validation-verified.
- No real banking data, external sanctions feed, production integrations, ML model or regulatory decision logic.
- No OpsTruth signed evidence receipt has been generated in this environment.

## 7. Responsible use
All records are synthetic. Monitoring thresholds are illustrative and unvalidated. An alert is a review prompt, not evidence of criminal activity, and cannot be used as an automated compliance decision. Do not add actual customer or bank data.
