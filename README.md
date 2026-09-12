# Global Retail E-Commerce — Data Warehouse & Analytics

3-Day Sprint-Based Data Engineering Capstone, built entirely on **Snowflake** (SQL + Snowpark Python + Streamlit-in-Snowflake).

## 📌 Project Objective
Design and build an end-to-end data warehouse for a global retail e-commerce company — from raw, messy OLTP-style CSV extracts to a validated Star Schema, with Full + Incremental ETL, SCD Type 2 history tracking, PII masking, error logging, and a live analytics dashboard.

## 🏗️ Architecture
```
RAW CSVs → RAW schema (as-is, VARCHAR) → STAGING schema (cleaned + validated + error-logged) → DW schema (Star Schema) → Analytics (Notebook + Streamlit Dashboard)
```

## ⭐ Star Schema
![Star Schema](DA-Project-Team-7/Schema.png)

- **FACT_SALES** — grain: one row per order item
- **DIM_CUSTOMER** — SCD Type 2 (tracks city/email/phone changes over time), email & phone masked
- **DIM_PRODUCT**, **DIM_DATE**, **DIM_LOCATION** — Type 1 dimensions

## 📂 Repository Structure
| Folder | Contents |
|---|---|
| `RawDataset/` | Original 5 source CSVs (customers, products, orders, order_items, payments) — ~1.4M rows, ~200K deliberately dirty |
| `CleanDataset/` | Final exported DW tables (dimensions + fact) after full ETL |
| `SF-CODE/` | All SQL scripts, run in numeric order (`00_` setup → `09_` validation) |
| `PY-Code/` | Snowpark analytics notebook + Streamlit dashboard app |
| `Schema.png` | Star schema diagram |
| `*.pptx` / `*.docx` | Final presentation and written report |

## 🔧 How to Reproduce
Run the SQL scripts in `SF-CODE/` **in numeric order** inside Snowsight worksheets:
1. `00_setup.sql` — creates database, schemas, warehouse, stage
2. Upload the 5 CSVs from `RawDataset/` into `RAW.*` tables (all columns as VARCHAR)
3. `00_fix_columns.sql` — renames auto-generated columns to real names if needed
4. `01_explore.sql` / `02_analysis.sql` — Day 1 exploration & analytical SQL
5. `03_staging_ddl.sql` → `04_full_load_staging.sql` — builds and populates the cleaned STAGING layer, with per-row rejection reasons logged to `*_ERRORS` tables
6. `05_dw_ddl.sql` → `06_dw_dml.sql` — builds and populates the DW Star Schema
7. `07_scd2_customer.sql` — SCD Type 2 demo (simulate a customer attribute change, verify history is preserved)
8. `08_incremental_load.sql` — incremental load demo using a watermark table
9. `09_validation_check.sql` — validates cleaned row counts against the dataset's own ground-truth `profiling_summary.json`

Then open `PY-Code/retail_capstone_analysis.ipynb` as a Snowflake Notebook, or deploy `PY-Code/streamlit_app.py` as a Streamlit-in-Snowflake app, both pointed at `RETAIL_CAPSTONE.DW`.

## ✅ Data Quality — Validated Against Ground Truth
Unlike a simple "run some WHERE clauses" cleaning pass, our STAGING layer's error detection was validated against the dataset generator's own `profiling_summary.json` (ground-truth counts of intentionally injected bad rows). Detection rates:

| Table | Planted Bad Rows | Our Detected | Match |
|---|---|---|---|
| Orders | 30,000 | 30,000 | Exact |
| Order Items | 118,000 | 118,000 | Exact |
| Payments | 20,000 | 20,000 | Exact |
| Products | 3,000 | 3,038 | ~99% |
| Customers | 29,000 | 23,422 | Explained gap (future-date decay — see report) |

## 🔐 Data Quality & Governance Features
- **Masking**: email and phone masked in `DIM_CUSTOMER` (`email_masked`, `phone_masked`)
- **Error Logging**: every rejected row is preserved in a dedicated `*_ERRORS` table with a specific, human-readable rejection reason (not silently dropped)
- **SCD Type 2**: full history preserved for customer attribute changes (`eff_start_date`, `eff_end_date`, `is_current`)

## 📊 Analytics
5 required chart types (line, bar, histogram, pie, horizontal bar) delivered two ways:
- Seaborn charts in the Snowpark notebook
- An interactive Altair-based Streamlit dashboard with live filters

## ⚙️ Optimization
`FACT_SALES` clustered by `date_sk` for date-range query pruning at scale (see report for Query Profile analysis).

## 👥 Team
Team 7 — DA Project