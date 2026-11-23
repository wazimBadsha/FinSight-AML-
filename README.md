# FinSight AML

**Financial Crime Transaction Monitoring & Analytics — synthetic-data portfolio demonstrator**

FinSight AML is an educational project showing how Python, SQL and Power BI can be combined to generate synthetic banking data, assess basic data quality, apply explainable transaction-monitoring heuristics and report alert patterns.

> **Important:** This is not a production AML system. All data is synthetic. Rules and thresholds are illustrative, unvalidated examples. An alert is not evidence of criminal activity and must never be treated as a compliance decision.

## What it demonstrates
- Reproducible synthetic customer and transaction generation.
- Data-quality checks for duplicates, orphan records, invalid amounts and missing attributes.
- Explainable heuristic alerts with scenario IDs and rationales.
- CSV outputs suitable for SQL exploration and Power BI.
- PostgreSQL reference schema and analytical queries.
- Automated tests for deterministic generation, quality checks, alert rules and output files.

## Quick start

Requirements: Python 3.11 or newer.

```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows PowerShell
.venv\Scripts\Activate.ps1

python -m pip install -e '.[test]'
python -m finsight_aml.pipeline --customers 250 --transactions 10000 --output data/generated
pytest -q
```

If running directly from the repository without installing the package:

```bash
PYTHONPATH=src python -m finsight_aml.pipeline
```

## Outputs
The pipeline generates `customers.csv`, `transactions.csv`, `data_quality_issues.csv`, `alerts.csv` and `run_summary.json` under `data/generated/`. Generated datasets are intentionally not committed; regenerate them locally.

## Repository map
- `src/finsight_aml/`: generator, quality checks, rule engine, CLI
- `database/`: PostgreSQL reference DDL and SQL analytics
- `docs/`: architecture, requirements, dictionary, methodology
- `dashboards/`: Power BI build guide
- `tests/`: automated tests

## Engineering notes
- The executable demo uses Python's standard library and writes CSV files.
- PostgreSQL assets are reference materials; a PostgreSQL adapter is not yet implemented.
- Amounts are not converted across currencies. Do not aggregate mixed-currency amounts as one monetary total.
- Seeded generation makes test runs reproducible; run timestamps in the summary are intentionally time-dependent.

## Next engineering increments
1. Add a PostgreSQL repository adapter and migration tooling.
2. Add a calendar dimension and properly defined rolling-window scenarios.
3. Add rule configuration files, rule versioning and unit tests per scenario.
4. Add a case lifecycle with investigator disposition and audit history.
5. Add calibrated metrics using a labelled synthetic evaluation set.
6. Build and validate a Power BI report before publishing a `.pbix`.

## Authoring guidance
This is a proposed independent portfolio project. Do not describe it as employer work, client delivery, production AML deployment or regulated model validation. Update the README with the contributor's actual work and screenshots after implementation.