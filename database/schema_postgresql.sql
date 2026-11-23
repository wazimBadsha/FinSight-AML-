-- PostgreSQL reference schema. Synthetic educational data only.
CREATE TABLE IF NOT EXISTS customers (
  customer_id TEXT PRIMARY KEY,
  customer_type TEXT NOT NULL CHECK (customer_type IN ('INDIVIDUAL','BUSINESS')),
  risk_band TEXT NOT NULL CHECK (risk_band IN ('LOW','MEDIUM','HIGH')),
  country CHAR(2) NOT NULL,
  kyc_complete BOOLEAN NOT NULL,
  created_at TIMESTAMPTZ NOT NULL
);
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id TEXT PRIMARY KEY,
  customer_id TEXT NOT NULL REFERENCES customers(customer_id),
  occurred_at TIMESTAMPTZ NOT NULL,
  amount NUMERIC(18,2) NOT NULL CHECK (amount > 0),
  currency CHAR(3) NOT NULL,
  transaction_type TEXT NOT NULL,
  counterparty_country CHAR(2) NOT NULL,
  channel TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS alerts (
  alert_id TEXT PRIMARY KEY,
  transaction_id TEXT NOT NULL REFERENCES transactions(transaction_id),
  customer_id TEXT NOT NULL REFERENCES customers(customer_id),
  scenario TEXT NOT NULL,
  severity TEXT NOT NULL CHECK (severity IN ('LOW','MEDIUM','HIGH')),
  rationale TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('OPEN','UNDER_REVIEW','CLOSED'))
);
CREATE INDEX IF NOT EXISTS idx_transactions_customer_time ON transactions(customer_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_transactions_type_amount ON transactions(transaction_type, amount);
CREATE INDEX IF NOT EXISTS idx_alerts_status_severity ON alerts(status, severity);
