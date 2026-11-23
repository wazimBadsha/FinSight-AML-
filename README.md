# FinSight AML

**Financial Crime Transaction Monitoring & Analytics — synthetic-data portfolio demonstrator**

FinSight AML is an educational project demonstrating how Python, SQL and Power BI can be combined to generate synthetic banking data, assess data quality, apply explainable transaction-monitoring heuristics and report alert patterns.

> **Important:** This is not a production AML system. All data is synthetic. Rules and thresholds are illustrative, unvalidated examples. An alert is not evidence of criminal activity and must never be treated as a compliance decision.

## Runtime modes

### Batch mode (default)
Suitable for small demonstrations and existing tests. It creates the requested data in memory before writing CSV output.

```bash
python -m finsight_aml.pipeline --customers 250 --transactions 10000 --output data/generated
```

### Streaming mode (long-running workloads)
Generates transactions in bounded batches, appends outputs incrementally, and writes a durable checkpoint after each batch. It avoids holding the full transaction population in memory.

```bash
python -m finsight_aml.pipeline --stream --customers 250 --transactions 1000000 --batch-size 5000 --output data/long-run
```

The process prints JSON progress lines and persists:
- `checkpoint.json`: completed transaction index and run configuration.
- `run_state.json`: progress percentage and status.
- `customers.csv`, `transactions.csv`, `alerts.csv`, `data_quality_issues.csv`: incremental outputs.

Stop with Ctrl+C or a SIGTERM. The current batch completes and the checkpoint is saved. Resume using the same parameters:

```bash
python -m finsight_aml.pipeline --stream --resume --customers 250 --transactions 1000000 --batch-size 5000 --output data/long-run
```

Do not change the customer count, transaction count or seed when resuming. The program rejects a mismatched checkpoint. Use a new output directory for a new run.

## Background process guidance

For a persistent server/worker, run this command under a process supervisor such as systemd, Supervisor, Docker restart policy or Kubernetes Job/CronJob according to the environment. The CLI itself does not daemonize or detach. GitHub Actions is a finite CI runner and is not a permanent background process host; workflow job timeouts and runner lifecycle are controlled by GitHub.

Example Linux systemd unit (adjust absolute paths and service account):

```ini
[Unit]
Description=FinSight AML synthetic data batch
After=network.target

[Service]
Type=oneshot
User=finsight
WorkingDirectory=/opt/finsight-aml
ExecStart=/opt/finsight-aml/.venv/bin/python -m finsight_aml.pipeline --stream --customers 250 --transactions 1000000 --batch-size 5000 --output /var/lib/finsight-aml/run
TimeoutStartSec=infinity
KillSignal=SIGTERM

[Install]
WantedBy=multi-user.target
```

For recurring independent runs, use a systemd timer or an external scheduler. For a continuously running service, implement a worker loop and supervisor explicitly; the current CLI is a finite data-generation job.

## What it demonstrates
- Reproducible synthetic customer and transaction generation.
- Data-quality checks for duplicate identifiers, orphan transactions, invalid amounts and missing attributes.
- Explainable heuristic alerts with scenario IDs and rationales.
- CSV outputs suitable for SQL exploration and Power BI.
- PostgreSQL reference schema and analytical queries.
- Automated tests for batch generation, streaming completion, interruption and resume.

## Setup
Requirements: Python 3.11 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'
pytest -q
```

## Limitations
- PostgreSQL assets are reference materials; a database adapter is not implemented.
- Power BI `.pbix` is not included; see `dashboards/powerbi-guide.md`.
- Amounts in different currencies must not be aggregated without a documented FX conversion.
- Thresholds are invented for demonstration and are not legal or regulatory thresholds.
- Alerts are review prompts, not findings of wrongdoing.
- The synthetic generator is not a behavioural model of a real bank.
