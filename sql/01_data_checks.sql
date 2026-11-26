-- Data quality checks after loading: row counts and business rules.
-- Every check should return its expected value.
SELECT 'customers'                          AS check_name, COUNT(*)::text AS result FROM customers
UNION ALL
SELECT 'accounts', COUNT(*)::text FROM accounts
UNION ALL
SELECT 'services', COUNT(*)::text FROM services
UNION ALL
SELECT 'customers without an account', COUNT(*)::text
FROM customers c
LEFT JOIN accounts a USING (customer_id)
WHERE a.customer_id IS NULL
UNION ALL
-- the 11 blank TotalCharges in the CSV were loaded as 0, all with tenure 0
SELECT 'zero total charges with tenure 0', COUNT(*)::text
FROM accounts
WHERE total_charges = 0 AND tenure_months = 0;
