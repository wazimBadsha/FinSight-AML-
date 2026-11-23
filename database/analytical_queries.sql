-- 1. Alert volumes by scenario and severity
SELECT scenario, severity, COUNT(*) AS alert_count
FROM alerts GROUP BY scenario, severity ORDER BY alert_count DESC;

-- 2. Customer transaction velocity over a rolling 30-day window
SELECT customer_id, occurred_at,
       COUNT(*) OVER (PARTITION BY customer_id ORDER BY occurred_at
         RANGE BETWEEN INTERVAL '30 days' PRECEDING AND CURRENT ROW) AS tx_count_30d,
       SUM(amount) OVER (PARTITION BY customer_id ORDER BY occurred_at
         RANGE BETWEEN INTERVAL '30 days' PRECEDING AND CURRENT ROW) AS tx_value_30d
FROM transactions;

-- 3. Customer KYC completeness and alert population
SELECT c.risk_band, c.kyc_complete, COUNT(DISTINCT c.customer_id) AS customers,
       COUNT(a.alert_id) AS alerts
FROM customers c LEFT JOIN alerts a ON a.customer_id = c.customer_id
GROUP BY c.risk_band, c.kyc_complete ORDER BY c.risk_band, c.kyc_complete;

-- 4. Alert ageing (assuming timestamps are stored in UTC)
SELECT status, severity, COUNT(*) AS alert_count
FROM alerts GROUP BY status, severity;
