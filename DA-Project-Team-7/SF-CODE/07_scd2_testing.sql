USE DATABASE RETAIL_CAPSTONE;

-- Step 1: pick one real customer and simulate a city change in STAGING
-- (as if a "refreshed" customer file arrived with updated info)
UPDATE STAGING.CUSTOMERS_CLEAN
SET city = 'Chennai'
WHERE customer_code = 'C0009857';   -- use any customer_code you can see exists

-- Step 2: confirm the change landed in STAGING
SELECT customer_code, city FROM STAGING.CUSTOMERS_CLEAN WHERE customer_code = 'C0009857';


SELECT customer_code, city, eff_start_date, eff_end_date, is_current
FROM DW.DIM_CUSTOMER
WHERE customer_code = 'C0009857'
ORDER BY eff_start_date;