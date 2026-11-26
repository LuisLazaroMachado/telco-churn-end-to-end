-- Contract x tenure churn matrix (the heat map from Excel and Power BI),
-- built as a pivot with conditional aggregation.
SELECT
    ct.name AS contract,
    ROUND(100.0 * AVG(a.churned::int) FILTER (WHERE a.tenure_months < 12), 2)                  AS "0-11",
    ROUND(100.0 * AVG(a.churned::int) FILTER (WHERE a.tenure_months BETWEEN 12 AND 23), 2)     AS "12-23",
    ROUND(100.0 * AVG(a.churned::int) FILTER (WHERE a.tenure_months BETWEEN 24 AND 35), 2)     AS "24-35",
    ROUND(100.0 * AVG(a.churned::int) FILTER (WHERE a.tenure_months BETWEEN 36 AND 47), 2)     AS "36-47",
    ROUND(100.0 * AVG(a.churned::int) FILTER (WHERE a.tenure_months BETWEEN 48 AND 59), 2)     AS "48-59",
    ROUND(100.0 * AVG(a.churned::int) FILTER (WHERE a.tenure_months >= 60), 2)                 AS "60-72"
FROM accounts a
JOIN contracts ct USING (contract_id)
GROUP BY ct.contract_id, ct.name
ORDER BY ct.contract_id;
