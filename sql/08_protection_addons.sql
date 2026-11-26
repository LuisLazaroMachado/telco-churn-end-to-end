-- Churn by number of protection add-ons (online security, online backup,
-- device protection, tech support) among internet customers.
WITH addons AS (
    SELECT
        a.churned,
        online_security::int + online_backup::int + device_protection::int + tech_support::int AS addon_count
    FROM services s
    JOIN accounts a USING (customer_id)
    WHERE s.internet_service <> 'No'
)
SELECT
    addon_count,
    COUNT(*)                            AS customers,
    ROUND(100.0 * AVG(churned::int), 2) AS churn_pct
FROM addons
GROUP BY addon_count
ORDER BY addon_count;
