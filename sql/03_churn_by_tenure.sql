-- Churn rate by tenure group (12-month buckets, 60-72 grouped together),
-- plus the running share of all churned customers.
WITH bucketed AS (
    SELECT LEAST(tenure_months / 12, 5) AS bucket, churned
    FROM accounts
)
SELECT
    CASE WHEN bucket = 5 THEN '60-72'
         ELSE (bucket * 12) || '-' || (bucket * 12 + 11) END            AS tenure_months,
    COUNT(*)                                                             AS customers,
    COUNT(*) FILTER (WHERE churned)                                      AS churned,
    ROUND(100.0 * AVG(churned::int), 2)                                  AS churn_pct,
    ROUND(100.0 * SUM(COUNT(*) FILTER (WHERE churned)) OVER (ORDER BY bucket)
          / SUM(COUNT(*) FILTER (WHERE churned)) OVER (), 2)             AS cumulative_share_of_churn_pct
FROM bucketed
GROUP BY bucket
ORDER BY bucket;
