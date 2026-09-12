-- A dedicated (small, cheap) virtual warehouse for this project
CREATE WAREHOUSE IF NOT EXISTS CAPSTONE_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60          -- turns off after 60 sec idle, saves credits
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE CAPSTONE_WH;

-- One database for the whole project
CREATE DATABASE IF NOT EXISTS RETAIL_CAPSTONE;
USE DATABASE RETAIL_CAPSTONE;

-- Three schemas = three layers of the pipeline
CREATE SCHEMA IF NOT EXISTS RAW;        -- untouched CSV data
CREATE SCHEMA IF NOT EXISTS STAGING;    -- cleaned + validated data
CREATE SCHEMA IF NOT EXISTS DW;         -- final star schema

-- A stage = upload folder, sitting inside RAW
CREATE STAGE IF NOT EXISTS RAW.CSV_STAGE
  FILE_FORMAT = (TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1);