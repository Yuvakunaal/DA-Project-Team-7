-- Run this truncate block first to clear out previous results before reloading
-- USE DATABASE RETAIL_CAPSTONE; USE SCHEMA STAGING;
-- TRUNCATE TABLE CUSTOMERS_CLEAN;   TRUNCATE TABLE CUSTOMERS_ERRORS;
-- TRUNCATE TABLE PRODUCTS_CLEAN;    TRUNCATE TABLE PRODUCTS_ERRORS;
-- TRUNCATE TABLE ORDERS_CLEAN;      TRUNCATE TABLE ORDERS_ERRORS;
-- TRUNCATE TABLE ORDER_ITEMS_CLEAN; TRUNCATE TABLE ORDER_ITEMS_ERRORS;
-- TRUNCATE TABLE PAYMENTS_CLEAN;    TRUNCATE TABLE PAYMENTS_ERRORS;

USE DATABASE RETAIL_CAPSTONE;

-- ============================================================
-- CUSTOMERS: checks Missing Values, Future Dates, Duplicate Keys, Type Mismatches
-- (unchanged — already correct)
-- ============================================================
CREATE OR REPLACE TEMPORARY TABLE _customers_flagged AS
SELECT *,
    ROW_NUMBER() OVER (PARTITION BY customer_code ORDER BY updated_at) AS rn,
    CASE
        WHEN customer_code IS NULL THEN 'missing_customer_code'
        WHEN city IS NULL OR TRIM(city) = '' THEN 'missing_city'
        WHEN email IS NULL OR TRIM(email) = '' THEN 'missing_email'
        WHEN phone IS NOT NULL AND NOT REGEXP_LIKE(phone, '.*[0-9].*') THEN 'phone_type_mismatch'
        WHEN full_name IS NULL OR TRIM(full_name) = '' THEN 'missing_name'
        WHEN TRY_TO_TIMESTAMP(updated_at) IS NULL THEN 'invalid_date_format'
        WHEN TRY_TO_TIMESTAMP(updated_at) > CURRENT_TIMESTAMP() THEN 'future_updated_at'
        ELSE NULL
    END AS reject_reason
FROM RAW.CUSTOMERS_RAW;

INSERT INTO STAGING.CUSTOMERS_CLEAN
SELECT customer_code, first_name, last_name, full_name, email, gender, city, state, phone,
       TRY_TO_TIMESTAMP(created_at), TRY_TO_TIMESTAMP(updated_at), TRY_TO_BOOLEAN(is_active)
FROM _customers_flagged
WHERE reject_reason IS NULL AND rn = 1;

INSERT INTO STAGING.CUSTOMERS_ERRORS (row_data, reason)
SELECT OBJECT_CONSTRUCT(* EXCLUDE (rn, reject_reason)),
       COALESCE(reject_reason, 'duplicate_customer_code')
FROM _customers_flagged
WHERE reject_reason IS NOT NULL OR rn > 1;

-- ============================================================
-- PRODUCTS: checks Missing Values, Negative Numbers, Duplicate Keys, Type Mismatches
-- (unchanged — already correct)
-- ============================================================
CREATE OR REPLACE TEMPORARY TABLE _products_flagged AS
SELECT *,
    ROW_NUMBER() OVER (PARTITION BY product_code ORDER BY product_name) AS rn,
    CASE
        WHEN product_code IS NULL THEN 'missing_product_code'
        WHEN product_name IS NULL OR TRIM(product_name) = '' THEN 'missing_name'
        WHEN category IS NULL OR TRIM(category) = '' THEN 'missing_category'
        WHEN TRY_TO_DECIMAL(TO_VARCHAR(unit_price), 18, 2) IS NULL THEN 'price_type_mismatch'
        WHEN TRY_TO_DECIMAL(TO_VARCHAR(unit_price), 18, 2) < 0 THEN 'negative_price'
        ELSE NULL
    END AS reject_reason
FROM RAW.PRODUCTS_RAW;

INSERT INTO STAGING.PRODUCTS_CLEAN
SELECT product_code, product_name, category,
       TRY_TO_DECIMAL(TO_VARCHAR(unit_price), 18, 2), TRY_TO_BOOLEAN(is_active)
FROM _products_flagged
WHERE reject_reason IS NULL AND rn = 1;

INSERT INTO STAGING.PRODUCTS_ERRORS (row_data, reason)
SELECT OBJECT_CONSTRUCT(* EXCLUDE (rn, reject_reason)),
       COALESCE(reject_reason, 'duplicate_product_code')
FROM _products_flagged
WHERE reject_reason IS NOT NULL OR rn > 1;

-- ============================================================
-- ORDERS: checks Missing Values, Future Dates, Duplicate Keys, Orphaned References
-- FIXED: tie-break on content issue instead of date, to avoid evicting real clean rows
-- ============================================================
CREATE OR REPLACE TEMPORARY TABLE _orders_flagged AS
WITH base AS (
    SELECT *,
        CASE
            WHEN order_id IS NULL THEN 'missing_order_id'
            WHEN customer_code = '__ORPHAN__' THEN 'orphan_customer'
            WHEN order_state IS NULL OR TRIM(order_state) = '' THEN 'missing_order_state'
            WHEN TRY_TO_TIMESTAMP(order_date) IS NULL THEN 'invalid_date_format'
            WHEN TRY_TO_TIMESTAMP(order_date) > CURRENT_TIMESTAMP() THEN 'future_order_date'
            ELSE NULL
        END AS content_issue
    FROM RAW.ORDERS_RAW
)
SELECT * EXCLUDE (content_issue),
    ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY IFF(content_issue IS NULL, 0, 1)) AS rn,
    content_issue AS reject_reason
FROM base;

INSERT INTO STAGING.ORDERS_CLEAN
SELECT order_id, customer_code, TRY_TO_TIMESTAMP(order_date), status, order_city, order_state
FROM _orders_flagged
WHERE reject_reason IS NULL AND rn = 1;

INSERT INTO STAGING.ORDERS_ERRORS (row_data, reason)
SELECT OBJECT_CONSTRUCT(* EXCLUDE (rn, reject_reason)),
       COALESCE(reject_reason, 'duplicate_order_id')
FROM _orders_flagged
WHERE reject_reason IS NOT NULL OR rn > 1;

-- ============================================================
-- ORDER_ITEMS: checks Missing Values, Negative Numbers, Duplicate Keys, Orphaned Refs, Type Mismatches
-- FIXED: tie-break on content issue instead of order_id
-- ============================================================
CREATE OR REPLACE TEMPORARY TABLE _order_items_flagged AS
WITH base AS (
    SELECT *,
        CASE
            WHEN order_item_id IS NULL THEN 'missing_order_item_id'
            WHEN order_id = '__ORPHAN__' THEN 'orphan_order'
            WHEN product_code = '__ORPHAN__' THEN 'orphan_product'
            WHEN quantity IS NULL THEN 'missing_quantity'
            WHEN quantity < 0 THEN 'negative_quantity'
            WHEN TRY_TO_DECIMAL(TO_VARCHAR(unit_price), 18, 2) IS NULL THEN 'price_type_mismatch'
            WHEN TRY_TO_DECIMAL(TO_VARCHAR(unit_price), 18, 2) < 0 THEN 'negative_unit_price'
            WHEN line_amount IS NULL THEN 'missing_line_amount'
            WHEN line_amount < 0 THEN 'negative_line_amount'
            ELSE NULL
        END AS content_issue
    FROM RAW.ORDER_ITEMS_RAW
)
SELECT * EXCLUDE (content_issue),
    ROW_NUMBER() OVER (PARTITION BY order_item_id ORDER BY IFF(content_issue IS NULL, 0, 1)) AS rn,
    content_issue AS reject_reason
FROM base;

INSERT INTO STAGING.ORDER_ITEMS_CLEAN
SELECT order_item_id, order_id, product_code,
       quantity, TRY_TO_DECIMAL(TO_VARCHAR(unit_price), 18, 2), line_amount
FROM _order_items_flagged
WHERE reject_reason IS NULL AND rn = 1;

INSERT INTO STAGING.ORDER_ITEMS_ERRORS (row_data, reason)
SELECT OBJECT_CONSTRUCT(* EXCLUDE (rn, reject_reason)),
       COALESCE(reject_reason, 'duplicate_order_item_id')
FROM _order_items_flagged
WHERE reject_reason IS NOT NULL OR rn > 1;

-- ============================================================
-- PAYMENTS: checks Missing Values, Negative Numbers, Future Dates, Duplicate Keys, Orphaned Refs, Type Mismatches
-- FIXED: tie-break on content issue instead of payment_date
-- ============================================================
CREATE OR REPLACE TEMPORARY TABLE _payments_flagged AS
WITH base AS (
    SELECT *,
        CASE
            WHEN payment_id IS NULL THEN 'missing_payment_id'
            WHEN order_id = '__ORPHAN__' THEN 'orphan_order'
            WHEN payment_method IS NULL OR TRIM(payment_method) = '' THEN 'missing_payment_method'
            WHEN TRY_TO_DECIMAL(TO_VARCHAR(payment_amount), 18, 2) IS NULL THEN 'amount_type_mismatch'
            WHEN TRY_TO_DECIMAL(TO_VARCHAR(payment_amount), 18, 2) < 0 THEN 'negative_payment_amount'
            WHEN TRY_TO_TIMESTAMP(payment_date) IS NULL THEN 'invalid_date_format'
            WHEN TRY_TO_TIMESTAMP(payment_date) > CURRENT_TIMESTAMP() THEN 'future_payment_date'
            ELSE NULL
        END AS content_issue
    FROM RAW.PAYMENTS_RAW
)
SELECT * EXCLUDE (content_issue),
    ROW_NUMBER() OVER (PARTITION BY payment_id ORDER BY IFF(content_issue IS NULL, 0, 1)) AS rn,
    content_issue AS reject_reason
FROM base;

INSERT INTO STAGING.PAYMENTS_CLEAN
SELECT payment_id, order_id, TRY_TO_DECIMAL(TO_VARCHAR(payment_amount), 18, 2),
       payment_method, TRY_TO_TIMESTAMP(payment_date)
FROM _payments_flagged
WHERE reject_reason IS NULL AND rn = 1;

INSERT INTO STAGING.PAYMENTS_ERRORS (row_data, reason)
SELECT OBJECT_CONSTRUCT(* EXCLUDE (rn, reject_reason)),
       COALESCE(reject_reason, 'duplicate_payment_id')
FROM _payments_flagged
WHERE reject_reason IS NOT NULL OR rn > 1;