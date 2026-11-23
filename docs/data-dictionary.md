# Data dictionary

## customers.csv
- `customer_id`: synthetic unique customer key.
- `customer_type`: INDIVIDUAL or BUSINESS.
- `risk_band`: synthetic LOW, MEDIUM or HIGH segment; not a calibrated risk score.
- `country`: fictional profile attribute represented by ISO-like country code.
- `kyc_complete`: synthetic completeness flag.
- `created_at`: synthetic customer creation timestamp.

## transactions.csv
- `transaction_id`: synthetic unique transaction key.
- `customer_id`: associated synthetic customer.
- `occurred_at`: UTC timestamp.
- `amount`: positive synthetic transaction amount.
- `currency`: synthetic currency code; amounts are not converted or aggregated across currencies in this demo.
- `transaction_type`: transaction category.
- `counterparty_country`: synthetic counterparty country.
- `channel`: BRANCH, ONLINE, MOBILE or ATM.

## alerts.csv
- `alert_id`: deterministic alert key.
- `transaction_id`, `customer_id`: linked synthetic records.
- `scenario`: monitoring rule identifier.
- `severity`: illustrative priority, not a regulatory classification.
- `rationale`: human-readable rule explanation.
- `status`: initial OPEN status.

## data_quality_issues.csv
- `severity`: illustrative issue priority.
- `issue`: issue code.
- `count`: aggregate count where applicable.
- `record_id`: associated record when applicable.
