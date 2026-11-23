# Detection methodology and responsible use

## Illustrative scenarios
1. `CASH_DEPOSIT_NEAR_THRESHOLD`: flags a synthetic cash deposit in the range [9,000, 10,000). This is a demonstration band, not a legal reporting threshold.
2. `HIGH_VALUE_TRANSFER`: flags a synthetic outgoing transfer of at least 15,000 units. Currency conversion is not performed, so do not compare amounts across currencies as if they were equivalent.
3. `HIGH_TRANSACTION_COUNT`: flags a customer with at least 45 transactions in the generated observation period. This is a simple population-level heuristic, not a rolling time-window rule.

## Validation requirements before any real-world use
- Obtain institution-specific policies and approved typologies.
- Calibrate thresholds using representative, legally permitted data.
- Test false-positive and false-negative rates with domain experts.
- Validate currency conversion, time zones, customer segmentation and peer groups.
- Establish model/rule governance, versioning, explainability and independent review.
- Keep human investigators responsible for case decisions.
- Conduct privacy, security, legal and regulatory reviews.

Alerts are prompts for review, not findings of wrongdoing. No person or organisation should be assessed using this synthetic demo.
