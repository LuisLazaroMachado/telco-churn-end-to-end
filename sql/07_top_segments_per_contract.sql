-- The three riskiest segments (internet service x payment method)
-- within each contract type, among segments with at least 50 customers.
WITH segments AS (
    SELECT
        ct.contract_id,
        ct.name                               AS contract,
        s.internet_service,
        pm.name                               AS payment_method,
        COUNT(*)                              AS customers,
        ROUND(100.0 * AVG(a.churned::int), 2) AS churn_pct
    FROM accounts a
    JOIN contracts ct       USING (contract_id)
    JOIN payment_methods pm USING (payment_method_id)
    JOIN services s         USING (customer_id)
    GROUP BY ct.contract_id, ct.name, s.internet_service, pm.name
    HAVING COUNT(*) >= 50
),
ranked AS (
    SELECT *, RANK() OVER (PARTITION BY contract_id ORDER BY churn_pct DESC) AS risk_rank
    FROM segments
)
SELECT contract, risk_rank, internet_service, payment_method, customers, churn_pct
FROM ranked
WHERE risk_rank <= 3
ORDER BY contract_id, risk_rank;
