-- The highest-risk group: new (under 12 months), month-to-month, fiber optic.
-- Needs three tables: accounts, contracts and services.
SELECT
    COUNT(*)                              AS customers,
    COUNT(*) FILTER (WHERE a.churned)     AS churned,
    ROUND(100.0 * AVG(a.churned::int), 2) AS churn_pct
FROM accounts a
JOIN contracts ct USING (contract_id)
JOIN services s USING (customer_id)
WHERE ct.name = 'Month-to-month'
  AND a.tenure_months < 12
  AND s.internet_service = 'Fiber optic';
