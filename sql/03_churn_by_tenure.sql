SELECT
    CASE MIN(tenure / 12, 5)
        WHEN 5 THEN '60-72'
        ELSE (MIN(tenure / 12, 5) * 12) || '-' || (MIN(tenure / 12, 5) * 12 + 11)
    END AS tenure_months,
    COUNT(*) AS customers,
    ROUND(100.0 * AVG(CASE WHEN Churn = 'Yes' THEN 1.0 ELSE 0 END), 2) AS churn_pct
FROM customers
GROUP BY MIN(tenure / 12, 5)
ORDER BY MIN(tenure / 12, 5);
