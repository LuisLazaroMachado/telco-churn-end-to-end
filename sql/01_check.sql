SELECT
    COUNT(*) AS customers,
    SUM(CASE WHEN TRIM(TotalCharges) = '' THEN 1 ELSE 0 END) AS blank_total_charges
FROM customers;
