USE DATABASE RETAIL_CAPSTONE; USE SCHEMA DW;

-- SCD Type 2 dimension: notice eff_start_date / eff_end_date / is_current
CREATE OR REPLACE TABLE DIM_CUSTOMER (
  customer_sk NUMBER AUTOINCREMENT PRIMARY KEY,   -- surrogate key
  customer_code STRING,                            -- business key
  full_name STRING,
  email_masked STRING,
  phone_masked STRING,
  gender STRING,
  city STRING,
  state STRING,
  is_active BOOLEAN,
  eff_start_date TIMESTAMP,
  eff_end_date TIMESTAMP,
  is_current BOOLEAN
);

CREATE OR REPLACE TABLE DIM_PRODUCT (
  product_sk NUMBER AUTOINCREMENT PRIMARY KEY,
  product_code STRING,
  product_name STRING,
  category STRING,
  unit_price NUMBER(18,2),
  is_active BOOLEAN
);

CREATE OR REPLACE TABLE DIM_LOCATION (
  location_sk NUMBER AUTOINCREMENT PRIMARY KEY,
  city STRING,
  state STRING
);

CREATE OR REPLACE TABLE DIM_DATE (
  date_sk NUMBER PRIMARY KEY,      -- format YYYYMMDD, e.g. 20250115
  full_date DATE,
  year NUMBER, quarter NUMBER, month NUMBER, month_name STRING,
  day NUMBER, day_of_week STRING, is_weekend BOOLEAN
);

CREATE OR REPLACE TABLE FACT_SALES (
  order_item_id STRING,
  order_id STRING,
  customer_sk NUMBER,
  product_sk NUMBER,
  location_sk NUMBER,
  date_sk NUMBER,
  quantity NUMBER,
  unit_price NUMBER(18,2),
  line_amount NUMBER(18,2),
  order_status STRING
);