Retail Analytics – Databricks Medallion Pipeline

License: MIT
Author: Kamil Soszka
Repository: https://github.com/kamilsoszka/retail-analytics-databricks

AI-Assisted Engineering – This project was developed with generative AI as a co-pilot, accelerating implementation from weeks to days while maintaining production-grade quality.

Overview

A production-grade, end-to-end data pipeline for retail transaction analytics built on 10 million synthetic sales rows. Implements Medallion architecture (Bronze -> Silver -> Gold) inside Databricks with Unity Catalog, Delta Lake, and Spark.

- 10 million synthetic sales rows (2023-01-01 to 2026-05-26) with realistic revenue trend: decline (60k->50k) -> flat -> strong rise to 95k daily net sales.
- End-to-end automation – from CSV ingestion to 17 analytical tables.
- Data quality checks + model validation (orphan keys, range, hour, delivery logic).
- 17 materialized analytical views – product margin, promotion uplift, RFM segmentation, returns, channel performance, Pareto, basket analysis, delivery impact, warranty/eco, hourly sales, recency impact, and more.

All percentage columns are stored as decimal fractions (e.g., 0.1196 = 11.96%). Negative margins are allowed.

Architecture – Medallion Layers

CSV files (from Volume)
   |
   v
Bronze (raw Delta)
- Explicit StructType schemas (no inferSchema)
- Audit columns: _source_file, _ingestion_ts
   |
   v
Silver (cleaned & standardised)
- Single-pass projection casting to DecimalType
- Negate qty for returns (prevents double COGS)
- Deduplicate on primary keys, coalesce partitions
   |
   v
Gold (17 analytical tables)
- Materialized Delta tables with aggregate-then-join CTEs
- Direct Lake ready for Power BI
   |
   v
Power BI / SQL Endpoint

Repository Structure

retail-analytics-databricks/
  .gitignore
  README.md
  csv/                                 (generated CSV files – ignored by Git)
  notebooks/
    00_run_all_pipeline.py
    01_ingest_bronze.py
    02_transform_silver.py
    03_create_gold_views.sql
    04_optimize_delta.py
    05_validate_silver_gold.sql
  reports/
    RetailAnalytics_Databricks.pbix   (optional, large file – ignored by Git)
  scripts/
    generate_retail_data.py

Data Generation Rules

- 10,000,000 fact rows with daily net sales target scaled to match a realistic trend.
- Dimensions: dim_date (1243), dim_customer (200k), dim_product (2000), dim_store (200), dim_promotion (101 including promoid=0). No dummy rows with -1.
- Margins distribution: 5% exactly 30%, 5% 20-29%, 5% exactly 15%, 50% 5-10%, 30% 0-5%, 5% negative (-10% to 0%).
- Returns: 2-8% return rate depending on channel. When isreturn = 1, qty is negated in the Silver layer.
- Hourly distribution: different probability curves for Online, Mobile App, Phone Order, and In-Store (extended hours for Convenience/Hypermarket).

How to Reproduce

Local data generation

1. Install dependencies: pip install pandas numpy
2. Run: python scripts/generate_retail_data.py
3. CSV files will be created in the csv/ folder.

Databricks Setup

- Create a catalog (e.g., retail_catalog) with Unity Catalog enabled.
- Create three schemas: 01_bronze, 02_silver, 03_gold.
- Create a volume (e.g., default.csv_files) and upload the CSV files to a subfolder raw.
- Use a running interactive cluster (not a SQL Warehouse).

Run Pipeline

1. Import all notebooks from the notebooks/ folder into your Databricks workspace.
2. Attach the cluster to 00_run_all_pipeline.
3. Run 00_run_all_pipeline. It will execute:
   - 01_ingest_bronze (loads CSV to Bronze)
   - 02_transform_silver (cleans and writes Silver)
   - 03_create_gold_views (creates 17 Gold tables)
   - 04_optimize_delta (optimizes Delta tables)
   - 05_validate_silver_gold (runs data quality checks)

Validation Queries (run manually in a SQL notebook)

-- 1. Aggregated revenue and margin by category and customer tier (top 5)
USE CATALOG retail_catalog;
SELECT p.category, c.tier, COUNT(*) AS transaction_count, ROUND(SUM(s.net), 2) AS total_revenue, ROUND(SUM(s.grossvalue - s.discountamount - (s.qty * p.unitcost)), 2) AS total_margin, CONCAT(CAST(ROUND(SUM(s.grossvalue - s.discountamount - (s.qty * p.unitcost)) / NULLIF(SUM(s.net), 0) * 100, 2) AS STRING), '%') AS margin_pct FROM `02_silver`.silver_factsales s INNER JOIN `02_silver`.silver_dimproduct p ON s.productid = p.productid INNER JOIN `02_silver`.silver_dimcustomer c ON s.customerid = c.customerid WHERE s.isreturn = 0 GROUP BY p.category, c.tier ORDER BY transaction_count DESC LIMIT 5;

-- 2. Product-level validation for specific products from vw_001
USE CATALOG retail_catalog;
SELECT name AS `Product Name`, ROUND(total_revenue, 2) AS `Revenue USD`, ROUND(total_cost, 2) AS `Cost USD`, ROUND(total_margin, 2) AS `Margin USD`, CONCAT(CAST(ROUND(margin_pct * 100, 2) AS STRING), '%') AS `Margin %`, rank_in_cat AS `Rank` FROM `03_gold`.vw_001_product_category_margin WHERE name IN ('Mattel Max Lego Set', 'Nerf Core Board Game Series 5', 'Mattel Studio Cart', 'Playmobil Mini Plushie V2', 'Playmobil Mini Action Figure Series 5') ORDER BY `Revenue USD` DESC, `Product Name` ASC;

Performance Optimisations

- Data generation: vectorised numpy/pandas, chunked writing.
- Bronze: explicit StructType schemas, lineage columns.
- Silver: single projection pass, coalesce, qty negation, deduplication.
- Gold: aggregate-then-join CTEs, materialized Delta tables.
- Delta maintenance: Z-Order on (datekey, productid, customerid) for silver_factsales, compaction for gold tables.

AI Contribution & Quality Assurance

The AI generated consistent code, refactored PySpark notebooks, fixed SQL syntax issues, and implemented defensive checks. Result: production-ready, minimal bugs, follows industry best practices.

License: MIT