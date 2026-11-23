# FinSight AML — Engineering Handoff

**Version:** 0.1.0  
**Delivery type:** Local portfolio MVP scaffold  
**Status:** Published to GitHub; CI and external evidence verification pending

## 1. Objective
Deliver a reproducible, synthetic-data analytics demonstrator that shows the flow from data generation through quality checks and explainable monitoring heuristics to Power BI-ready outputs.

## 2. Delivered components
- Python package under `src/finsight_aml/`.
- Deterministic synthetic customer and transaction generator.
- Data-quality checks.
- Three explainable monitoring heuristics.
- CSV exports and run summary generated at runtime (generated datasets are not committed).
- PostgreSQL reference schema and analytical SQL.
- Power BI dashboard implementation guide.
- Automated tests.
- Architecture, requirements, data dictionary and responsible-use documentation.
- GitHub Actions workflow for Python tests and a pipeline smoke test.

## 3. Run instructions
```bash
python -m venv .venv
source .venv/bin/activate                 # Windows: .venv\\Scripts\\Activate.ps1
python -m pip install -e '.[test]'
python -m finsight_aml.pipeline --customers 250 --transactions 10000 --output data/generated
pytest -q
```

## 4. Local verification evidence
The supplied delivery notes report local verification on 2026-11-23 using Python 3.13.5:
- Python test suite: 5 passed.
- Pipeline smoke test: generated 40 customers / 1,200 transactions and expected outputs.
- Standard sample: 250 customers / 10,000 transactions.
- Sample alert count: 79.
- Generated sample data-quality issue count: 0.
- Python compilation and ZIP integrity: passed.

These are prior local verification claims from the delivery bundle. They are not a fresh GitHub Actions result or independent OpsTruth receipt.

## 5. Known limitations / open work
- PostgreSQL schema and queries are reference assets, not wired into the executable pipeline.
- Power BI `.pbix` file is not included; only an implementation guide and DAX examples are provided.
- No real banking data, external sanctions lists, production integrations, ML model or regulatory decision logic.
- Rules are illustrative and not calibrated or validated.
- No authentication, authorization, deployment, observability or production security controls are implemented because this is a local portfolio demonstrator.
- GitHub Actions must complete successfully on the published commit before CI is marked verified.

## 6. Security and privacy
- No real personal, banking or customer data should be added to the repository.
- Do not commit credentials, tokens, connection strings or private datasets.
- Keep generated data clearly labelled synthetic.
- Review dependencies and license obligations before adding third-party packages.

## 7. Handoff acceptance criteria
- [x] Python pipeline and tests included in repository.
- [x] Generated datasets excluded from version control.
- [x] PostgreSQL reference schema and queries included.
- [x] Power BI implementation guide included.
- [ ] PostgreSQL DDL executes on a supported PostgreSQL instance.
- [ ] SQL queries execute against loaded sample data.
- [ ] Power BI report is built and reviewed; screenshots and `.pbix` are committed only after verification.
- [ ] GitHub Actions checks pass on the published commit.
- [ ] OpsTruth repository and CI evidence audit completed.

## 8. Scope statement
This is an educational analytics project, not a production financial-crime control. Alerts are review prompts only; they do not establish wrongdoing or replace qualified compliance investigation.
