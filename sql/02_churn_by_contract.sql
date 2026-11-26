-- Churn rate by contract type, with each contract's share of the customer base.
SELECT
    ct.name                                                     AS contract,
    COUNT(*)                                                    AS customers,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2)          AS share_of_customers_pct,
    COUNT(*) FILTER (WHERE a.churned)                           AS churned,
    ROUND(100.0 * AVG(a.churned::int), 2)                       AS churn_pct
FROM accounts a
JOIN contracts ct USING (contract_id)
GROUP BY ct.contract_id, ct.name
ORDER BY ct.contract_id;
