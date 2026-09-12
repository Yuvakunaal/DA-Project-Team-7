USE DATABASE RETAIL_CAPSTONE;

-- Step A: expire the OLD version of any customer whose city/email/phone changed
UPDATE DW.DIM_CUSTOMER dc
SET eff_end_date = CURRENT_TIMESTAMP(), is_current = FALSE
FROM STAGING.CUSTOMERS_CLEAN sc
WHERE dc.customer_code = sc.customer_code
  AND dc.is_current = TRUE
  AND (dc.city <> sc.city
       OR dc.email_masked <> REGEXP_REPLACE(sc.email, '^(.)([^@]*)(@.*)$', '\\1***\\3')
       OR dc.phone_masked <> CONCAT(REPEAT('*', GREATEST(LENGTH(sc.phone)-4,0)), RIGHT(sc.phone,4)));

-- Step B: insert the NEW version as current for anyone just expired, or brand new
INSERT INTO DW.DIM_CUSTOMER
  (customer_code, full_name, email_masked, phone_masked, gender, city, state,
   is_active, eff_start_date, eff_end_date, is_current)
SELECT sc.customer_code, sc.full_name,
       REGEXP_REPLACE(sc.email, '^(.)([^@]*)(@.*)$', '\\1***\\3'),
       CONCAT(REPEAT('*', GREATEST(LENGTH(sc.phone)-4,0)), RIGHT(sc.phone,4)),
       sc.gender, sc.city, sc.state, sc.is_active,
       CURRENT_TIMESTAMP(), NULL, TRUE
FROM STAGING.CUSTOMERS_CLEAN sc
LEFT JOIN DW.DIM_CUSTOMER dc
       ON sc.customer_code = dc.customer_code AND dc.is_current = TRUE
WHERE dc.customer_code IS NULL;   -- either brand new, or was just expired above