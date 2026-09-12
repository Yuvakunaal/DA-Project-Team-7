-- USE DATABASE RETAIL_CAPSTONE; USE SCHEMA DW;
-- TRUNCATE TABLE DIM_CUSTOMER;
-- TRUNCATE TABLE DIM_PRODUCT;
-- TRUNCATE TABLE DIM_LOCATION;
-- TRUNCATE TABLE FACT_SALES;
-- DIM_DATE does NOT need truncating — it's just a calendar, unaffected by this fix


USE DATABASE RETAIL_CAPSTONE;

-- Populate DIM_DATE (one-time, covers 3 years)
INSERT INTO DW.DIM_DATE
SELECT
  TO_NUMBER(TO_CHAR(d, 'YYYYMMDD')) AS date_sk,
  d AS full_date,
  YEAR(d), QUARTER(d), MONTH(d), MONTHNAME(d),
  DAY(d), DAYNAME(d),
  CASE WHEN DAYOFWEEK(d) IN (0,6) THEN TRUE ELSE FALSE END
FROM (
  SELECT DATEADD(day, SEQ4(), '2023-01-01') AS d
  FROM TABLE(GENERATOR(ROWCOUNT => 1500))
);


-- DIM_PRODUCT (Type 1 — simple overwrite, no history needed here)
INSERT INTO DW.DIM_PRODUCT (product_code, product_name, category, unit_price, is_active)
SELECT product_code, product_name, category, unit_price, is_active
FROM STAGING.PRODUCTS_CLEAN;

-- DIM_LOCATION — unique city/state pairs seen in orders
INSERT INTO DW.DIM_LOCATION (city, state)
SELECT DISTINCT order_city, order_state FROM STAGING.ORDERS_CLEAN
WHERE order_city IS NOT NULL;

-- DIM_CUSTOMER — first-ever load, every customer becomes "current"
INSERT INTO DW.DIM_CUSTOMER
  (customer_code, full_name, email_masked, phone_masked, gender, city, state,
   is_active, eff_start_date, eff_end_date, is_current)
SELECT
  customer_code, full_name,
  -- masking: keep first char + domain, blur the rest -> e.g. n***@example.net
  REGEXP_REPLACE(email, '^(.)([^@]*)(@.*)$', '\\1***\\3'),
  -- masking: keep last 4 digits only
  CONCAT(REPEAT('*', GREATEST(LENGTH(phone)-4,0)), RIGHT(phone,4)),
  gender, city, state, is_active,
  created_at, NULL, TRUE
FROM STAGING.CUSTOMERS_CLEAN;


-- Full Load into FACT_SALES
INSERT INTO DW.FACT_SALES
SELECT
  oi.order_item_id, oi.order_id,
  dc.customer_sk, dp.product_sk, dl.location_sk,
  TO_NUMBER(TO_CHAR(o.order_date, 'YYYYMMDD')),
  oi.quantity, oi.unit_price, oi.line_amount, o.status
FROM STAGING.ORDER_ITEMS_CLEAN oi
JOIN STAGING.ORDERS_CLEAN o   ON oi.order_id = o.order_id
JOIN DW.DIM_CUSTOMER dc       ON o.customer_code = dc.customer_code AND dc.is_current = TRUE
JOIN DW.DIM_PRODUCT dp        ON oi.product_code = dp.product_code
LEFT JOIN DW.DIM_LOCATION dl  ON o.order_city = dl.city AND o.order_state = dl.state;

--
SELECT COUNT(*) FROM DW.FACT_SALES;