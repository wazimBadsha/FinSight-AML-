# Power BI dashboard build guide

Import `customers.csv`, `transactions.csv`, `alerts.csv` and `data_quality_issues.csv` from `data/generated/`.

## Relationships
- `customers[customer_id]` 1-to-many `transactions[customer_id]`.
- `customers[customer_id]` 1-to-many `alerts[customer_id]`.
- `transactions[transaction_id]` 1-to-many `alerts[transaction_id]`.

Use single-direction filtering from dimensions to facts where possible. Add a proper calendar table for time analysis. Do not sum amounts across currencies without first converting them using a documented FX source and date convention.

## Suggested pages
1. Executive overview: customers, transactions, alerts, quality exceptions.
2. Monitoring: alerts by scenario, severity, channel and time.
3. Customer profile: risk band, country, KYC completeness.
4. Data quality: issue category, severity and record-level exceptions.

## Example DAX measures
```DAX
Total Transactions = COUNTROWS(Transactions)
Total Customers = DISTINCTCOUNT(Customers[customer_id])
Total Alerts = COUNTROWS(Alerts)
Open Alerts = CALCULATE([Total Alerts], Alerts[status] = "OPEN")
KYC Incomplete Customers = CALCULATE([Total Customers], Customers[kyc_complete] = FALSE())
```

The dashboard should label all data as synthetic and all alerts as illustrative.
