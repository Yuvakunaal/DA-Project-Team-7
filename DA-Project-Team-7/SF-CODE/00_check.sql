USE DATABASE RETAIL_CAPSTONE; USE SCHEMA RAW;

SELECT 'Customers' as table_name, COUNT(*) as count_rows FROM CUSTOMERS_RAW
UNION ALL
SELECT 'Products' as table_name, COUNT(*) as count_rows FROM PRODUCTS_RAW
UNION ALL
SELECT 'Orders' as table_name, COUNT(*) as count_rows FROM ORDERS_RAW
UNION ALL
SELECT 'Order_Items' as table_name, COUNT(*) as count_rows FROM ORDER_ITEMS_RAW
UNION ALL
SELECT 'Payments' as table_name, COUNT(*) as count_rows FROM PAYMENTS_RAW;

SELECT * FROM CUSTOMERS_RAW LIMIT 10;