-- Monthly revenue lost to churn, by contract.
-- Uses the monthly charges of customers who left.
WITH revenue AS (
    SELECT
        ct.name                                              AS contract,
        SUM(a.monthly_charges)                               AS monthly_revenue,
        SUM(a.monthly_charges) FILTER (WHERE a.churned)      AS monthly_revenue_lost
    FROM accounts a
    JOIN contracts ct USING (contract_id)
    GROUP BY ct.contract_id, ct.name
)
SELECT
    contract,
    monthly_revenue,
    monthly_revenue_lost,
    ROUND(100.0 * monthly_revenue_lost / monthly_revenue, 2)                  AS lost_pct_of_contract_revenue,
    ROUND(100.0 * monthly_revenue_lost / SUM(monthly_revenue_lost) OVER (), 2) AS share_of_all_revenue_lost_pct
FROM revenue
ORDER BY monthly_revenue_lost DESC;
