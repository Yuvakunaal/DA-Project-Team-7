USE DATABASE RETAIL_CAPSTONE; USE SCHEMA STAGING;

CREATE OR REPLACE TABLE CUSTOMERS_CLEAN (
  customer_code STRING, first_name STRING, last_name STRING, full_name STRING,
  email STRING, gender STRING, city STRING, state STRING, phone STRING,
  created_at TIMESTAMP, updated_at TIMESTAMP, is_active BOOLEAN
);

CREATE OR REPLACE TABLE PRODUCTS_CLEAN (
  product_code STRING, product_name STRING, category STRING,
  unit_price NUMBER(18,2), is_active BOOLEAN
);

CREATE OR REPLACE TABLE ORDERS_CLEAN (
  order_id STRING, customer_code STRING, order_date TIMESTAMP,
  status STRING, order_city STRING, order_state STRING
);

CREATE OR REPLACE TABLE ORDER_ITEMS_CLEAN (
  order_item_id STRING, order_id STRING, product_code STRING,
  quantity NUMBER, unit_price NUMBER(18,2), line_amount NUMBER(18,2)
);

CREATE OR REPLACE TABLE PAYMENTS_CLEAN (
  payment_id STRING, order_id STRING, payment_amount NUMBER(18,2),
  payment_method STRING, payment_date TIMESTAMP
);

-- One error-log table per source, so you can show *why* a row was rejected
CREATE OR REPLACE TABLE CUSTOMERS_ERRORS   (row_data VARIANT, reason STRING, logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE PRODUCTS_ERRORS    (row_data VARIANT, reason STRING, logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE ORDERS_ERRORS      (row_data VARIANT, reason STRING, logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE ORDER_ITEMS_ERRORS (row_data VARIANT, reason STRING, logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP());
CREATE OR REPLACE TABLE PAYMENTS_ERRORS    (row_data VARIANT, reason STRING, logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP());