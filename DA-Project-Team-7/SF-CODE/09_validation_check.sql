USE DATABASE RETAIL_CAPSTONE; USE SCHEMA STAGING;

SELECT COUNT(*) AS customers_clean_count FROM CUSTOMERS_CLEAN;
SELECT COUNT(*) AS customers_errors_count FROM CUSTOMERS_ERRORS;

SELECT COUNT(*) AS products_clean_count FROM PRODUCTS_CLEAN;
SELECT COUNT(*) AS products_errors_count FROM PRODUCTS_ERRORS;

SELECT COUNT(*) AS orders_clean_count FROM ORDERS_CLEAN;
SELECT COUNT(*) AS orders_errors_count FROM ORDERS_ERRORS;

SELECT COUNT(*) AS order_items_clean_count FROM ORDER_ITEMS_CLEAN;
SELECT COUNT(*) AS order_items_errors_count FROM ORDER_ITEMS_ERRORS;

SELECT COUNT(*) AS payments_clean_count FROM PAYMENTS_CLEAN;
SELECT COUNT(*) AS payments_errors_count FROM PAYMENTS_ERRORS;


SELECT reason, COUNT(*) AS cnt FROM PAYMENTS_ERRORS GROUP BY reason ORDER BY cnt DESC;
SELECT reason, COUNT(*) AS cnt FROM ORDER_ITEMS_ERRORS GROUP BY reason ORDER BY cnt DESC;
SELECT reason, COUNT(*) AS cnt FROM ORDERS_ERRORS GROUP BY reason ORDER BY cnt DESC;


-- === 
USE DATABASE RETAIL_CAPSTONE; USE SCHEMA RAW;

-- How many distinct payment_id values are duplicated, and how many "extra" rows do they create?
SELECT COUNT(*) AS distinct_duplicated_ids
FROM (SELECT payment_id FROM PAYMENTS_RAW GROUP BY payment_id HAVING COUNT(*) > 1);

SELECT SUM(cnt - 1) AS total_extra_duplicate_rows
FROM (SELECT payment_id, COUNT(*) AS cnt FROM PAYMENTS_RAW GROUP BY payment_id HAVING COUNT(*) > 1) t;

-- Same check for orders and order_items
SELECT SUM(cnt - 1) AS total_extra_duplicate_orders
FROM (SELECT order_id, COUNT(*) AS cnt FROM ORDERS_RAW GROUP BY order_id HAVING COUNT(*) > 1) t;

SELECT SUM(cnt - 1) AS total_extra_duplicate_order_items
FROM (SELECT order_item_id, COUNT(*) AS cnt FROM ORDER_ITEMS_RAW GROUP BY order_item_id HAVING COUNT(*) > 1) t;


-- DELETE FROM RAW.ORDERS_RAW WHERE ORDER_ID = 'order_id';
-- DELETE FROM RAW.PAYMENTS_RAW WHERE PAYMENT_ID = 'payment_id';