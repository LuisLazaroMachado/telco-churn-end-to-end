SELECT
    Contract,
    COUNT(*) AS customers,
    SUM(CASE WHEN Churn = 'Yes' THEN 1 ELSE 0 END) AS churned,
    ROUND(100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0 END), 2) AS churn_pct
FROM customers
GROUP BY Contract
ORDER BY churn_pct DESC;
