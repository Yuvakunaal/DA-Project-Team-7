USE DATABASE RETAIL_CAPSTONE; USE SCHEMA RAW;

-- Orphan customers referenced by orders
SELECT COUNT(*) AS orphan_orders
FROM ORDERS_RAW WHERE customer_code = '__ORPHAN__';

-- Orphan products referenced by order_items
SELECT COUNT(*) AS orphan_items
FROM ORDER_ITEMS_RAW WHERE product_code = '__ORPHAN__';

-- Orphan orders referenced by payments
SELECT COUNT(*) AS orphan_payments
FROM PAYMENTS_RAW WHERE order_id = '__ORPHAN__';

-- Duplicate customer_codes
SELECT CUSTOMER_CODE, COUNT(*) as duplicate_count
FROM CUSTOMERS_RAW GROUP BY CUSTOMER_CODE HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC LIMIT 20;

-- Rows where unit_price is NOT a valid number (type mismatch, e.g. "FREE")
SELECT PRODUCT_CODE, UNIT_PRICE
FROM PRODUCTS_RAW
WHERE TRY_TO_DECIMAL(UNIT_PRICE, 18, 2) IS NULL AND UNIT_PRICE IS NOT NULL
LIMIT 20;

-- Negative quantities
SELECT COUNT(*) as negative_quantities FROM ORDER_ITEMS_RAW WHERE QUANTITY < 0;

-- Future-dated updates (customer updated_at after today)
SELECT COUNT(*) as customers_updated_after_today FROM CUSTOMERS_RAW
WHERE TRY_TO_TIMESTAMP(UPDATED_AT) > CURRENT_TIMESTAMP();