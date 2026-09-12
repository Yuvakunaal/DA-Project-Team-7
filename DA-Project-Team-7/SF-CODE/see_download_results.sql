USE DATABASE RETAIL_CAPSTONE; USE SCHEMA DW;

select count(*) from dim_customer;
SELECT * FROM dim_customer LIMIT 350000;

select count(*) from dim_date;
SELECT * FROM dim_date LIMIT 350000;

select count(*) from dim_location;
SELECT * FROM dim_location LIMIT 350000;

select count(*) from dim_product;
SELECT * FROM dim_product LIMIT 350000;

select count(*) from fact_sales;
SELECT * FROM FACT_SALES LIMIT 350000;
SELECT * FROM FACT_SALES LIMIT 350000 OFFSET 350000;