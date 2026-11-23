# FinSight AML — Engineering Handoff

**Version:** 0.1.0  
**Delivery type:** Local portfolio MVP scaffold  
**Status:** Published to public GitHub repository; Python CI passed on implementation commit

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

## 4. Verification evidence

### Local verification
The project was run locally on 2026-11-23:
- Python test suite: 5 passed.
- Pipeline smoke test: generated 40 customers / 1,200 transactions and expected outputs.
- Standard sample: 250 customers / 10,000 transactions.
- Sample alert count: 79.
- Generated sample data-quality issue count: 0.
- Python compilation and ZIP integrity: passed.

### GitHub Actions verification
- Workflow: `tests`
- Job: `python-tests`
- Implementation commit tested: `075b9e4352e5fbd1e2cb387d5993c843f18875d6`
- Workflow run: [45220168398](https://github.com/wazimBadsha/FinSight-AML-/actions/runs/45220168398)
- Result: **SUCCESS**
- Verified steps: dependency installation, `pytest -q`, and pipeline smoke test.

This is CI evidence for the implementation commit above. The subsequent documentation-only handoff update triggers a new workflow run; check the Actions page for its result before treating the current HEAD as CI-verified.

## 5. Known limitations / open work
- PostgreSQL schema and queries are reference assets, not wired into the executable pipeline.
- Power BI `.pbix` file is not included; only an implementation guide and DAX examples are provided.
- No real banking data, external sanctions lists, production integrations, ML model or regulatory decision logic.
- Rules are illustrative and not calibrated or validated.
- No authentication, authorization, deployment, observability or production security controls are implemented because this is a local portfolio demonstrator.
- PostgreSQL DDL/query execution and Power BI report validation have not been performed.
- No independent OpsTruth receipt or signed evidence snapshot has been generated.

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
- [x] GitHub Actions passed on implementation commit `075b9e4`.
- [ ] Current documentation HEAD GitHub Actions run completes successfully.
- [ ] PostgreSQL DDL executes on a supported PostgreSQL instance.
- [ ] SQL queries execute against loaded sample data.
- [ ] Power BI report is built and reviewed; screenshots and `.pbix` are committed only after verification.
- [ ] OpsTruth repository and CI evidence audit completed.

## 8. Scope statement
This is an educational analytics project, not a production financial-crime control. Alerts are review prompts only; they do not establish wrongdoing or replace qualified compliance investigation.
