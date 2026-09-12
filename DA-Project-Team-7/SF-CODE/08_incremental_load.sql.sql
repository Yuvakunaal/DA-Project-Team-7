USE DATABASE RETAIL_CAPSTONE;
USE SCHEMA STAGING;

-- Step 1: create the watermark control table (one row per source table)
CREATE OR REPLACE TABLE LOAD_WATERMARKS (
  table_name STRING,
  last_loaded_at TIMESTAMP
);

-- Step 2: seed it — pretend we've never loaded anything before today
INSERT INTO LOAD_WATERMARKS VALUES
  ('ORDERS', '1900-01-01'::TIMESTAMP),
  ('PAYMENTS', '1900-01-01'::TIMESTAMP),
  ('CUSTOMERS', '1900-01-01'::TIMESTAMP);

-- Step 3: check current row count BEFORE incremental load (for comparison)
SELECT COUNT(*) AS orders_clean_before FROM ORDERS_CLEAN;

-- Step 4: simulate 1 new order arriving in RAW that wasn't there during the full load
INSERT INTO RAW.ORDERS_RAW (ORDER_ID, CUSTOMER_CODE, ORDER_DATE, STATUS, ORDER_CITY, ORDER_STATE)
VALUES ('SIM-ORDER-001', 'C0009857', TO_VARCHAR(CURRENT_TIMESTAMP()), 'COMPLETED', 'Mumbai', 'Maharashtra');

-- Step 5: move the watermark to a point in the past, so this new row counts as "new"
UPDATE LOAD_WATERMARKS
SET last_loaded_at = DATEADD('minute', -10, CURRENT_TIMESTAMP())
WHERE table_name = 'ORDERS';

-- Step 6: run the actual incremental pull (only rows newer than the watermark)
INSERT INTO STAGING.ORDERS_CLEAN
SELECT order_id, customer_code, TRY_TO_TIMESTAMP(order_date), status, order_city, order_state
FROM RAW.ORDERS_RAW
WHERE customer_code <> '__ORPHAN__'
  AND TRY_TO_TIMESTAMP(order_date) > (SELECT last_loaded_at FROM LOAD_WATERMARKS WHERE table_name='ORDERS')
  AND TRY_TO_TIMESTAMP(order_date) <= CURRENT_TIMESTAMP();

-- Step 7: move the watermark forward, marking this batch as "done"
UPDATE LOAD_WATERMARKS SET last_loaded_at = CURRENT_TIMESTAMP() WHERE table_name = 'ORDERS';

-- Step 8: verify it worked
SELECT COUNT(*) AS orders_clean_after FROM ORDERS_CLEAN;   -- should be +1 vs Step 3
SELECT * FROM ORDERS_CLEAN WHERE order_id = 'SIM-ORDER-001';
select * from LOAD_WATERMARKS;


--=====---=====
--=====---=====
-- WHEN YOU WANNA RUN THE ABOVE SCRIPT AGAIN, RUN BELOW SCRIPTS AND COMMENT AND RUN.
DELETE FROM RAW.ORDERS_RAW WHERE ORDER_ID = 'SIM-ORDER-001';
DELETE FROM STAGING.ORDERS_CLEAN WHERE order_id = 'SIM-ORDER-001';