# Architecture

FinSight AML is a small, reproducible portfolio demonstrator. It generates deterministic synthetic customers and transactions, runs basic data-quality checks, applies transparent heuristic monitoring scenarios, and exports CSV datasets for SQL exploration and Power BI.

## Data flow
1. `generate_records()` creates fictional customer and transaction records with a fixed seed.
2. `assess_quality()` checks duplicate customer identifiers, orphan transactions, non-positive amounts and missing key attributes.
3. `detect_alerts()` applies three illustrative rules: cash deposits in a configured near-threshold band, high-value outgoing transfers, and high transaction count over the generated observation period.
4. CSV outputs are written to `data/generated/`.
5. PostgreSQL DDL and analytical SQL are provided separately as a reference for a database-backed extension.
6. Power BI can import the generated CSVs and use the documented relationships and measures.

## Current scope and limitations
- The executable pipeline is local and uses only the Python standard library.
- PostgreSQL schema and queries are reference assets; the current automated pipeline does not connect to PostgreSQL.
- No ML model, sanctions-list feed, real customer data, production alert workflow or regulatory decisioning is implemented.
- Thresholds are invented for demonstration and are not regulatory thresholds or validated typologies.
- The synthetic records do not model realistic customer behaviour comprehensively.
