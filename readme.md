Retail Analytics Medallion Pipeline

License: MIT
Author: Kamil Soszka
Repository: https://github.com/kamilsoszka/retail-analytics-databricks

AI-Assisted Engineering – This project was developed with generative AI as a co-pilot, accelerating implementation from weeks to days while maintaining production-grade quality. It showcases modern data engineering practices and is a valuable portfolio piece for data professionals.

Project Overview

This project processes 10 million synthetic retail sales rows through a Medallion architecture (Bronze -> Silver -> Gold) in Databricks. It demonstrates end-to-end data engineering: ingestion, cleaning, transformation, optimization, and validation. The final output includes 17 analytical tables that answer key business questions (product margin, promotion uplift, customer RFM, returns analysis, etc.). This is a high-value, production-ready pipeline that can be adapted to real-world retail data.

Key Deliverables

- 10 million synthetic sales transactions with realistic trends
- Three-layer Medallion schema (01_bronze, 02_silver, 03_gold)
- Unified orchestrator notebook (00_run_all_pipeline)
- Delta Lake optimizations: Z-Order and bin-packing for performance
- 17 business-ready SQL views (e.g., margin, promo performance, RFM)
- Data quality validation suite
- Optional Power BI report (RetailAnalytics_Databricks.pbix)

Repository Structure

retail-analytics-databricks/
├── .gitignore
├── README.md
├── csv/                                 (folder with generated CSV files – ignored by Git due to large size)
├── notebooks/
│   ├── 00_run_all_pipeline.py
│   ├── 01_ingest_bronze.py
│   ├── 02_transform_silver.py
│   ├── 03_create_gold_views.sql
│   ├── 04_optimize_delta.py
│   └── 05_validate_silver_gold.sql
├── reports/
│   └── RetailAnalytics_Databricks.pbix
└── scripts/
    └── generate_retail_data.py

Step 1: Generate Synthetic Data

pip install pandas numpy
python scripts/generate_retail_data.py

This creates the csv/ folder with six CSV files (dim_date, dim_customer, dim_product, dim_store, dim_promotion, fact_sales). The fact_sales.csv is about 1 GB and is ignored by Git.

Step 2: Databricks Setup

- Create a catalog named 'retail_catalog' (or use an existing one).
- Create three schemas: '01_bronze', '02_silver', '03_gold'.
- Create a volume 'csv_files/raw' under the default schema.
- Upload the CSV files from your local csv/ folder to the volume path: /Volumes/retail_catalog/default/csv_files/raw/
- Use a running interactive cluster (Shared or Single Node). Do not use a SQL Warehouse because the pipeline includes Python notebooks.

Step 3: Run the Pipeline

1. Import all files from the 'notebooks/' directory into your Databricks workspace.
2. Attach your cluster to the orchestrator notebook '00_run_all_pipeline'.
3. Execute '00_run_all_pipeline'. It will run the following notebooks in order:
   - 01_ingest_bronze.py (loads CSV into Bronze Delta tables)
   - 02_transform_silver.py (cleans and writes Silver tables)
   - 03_create_gold_views.sql (creates 17 Gold tables)
   - 04_optimize_delta.py (runs OPTIMIZE and Z-ORDER)
   - 05_validate_silver_gold.sql (performs data quality checks)

After successful execution, you can query the Gold tables directly, for example:
SELECT * FROM retail_catalog.`03_gold`.vw_001_product_category_margin LIMIT 100;

Step 4: Validation Queries (optional, run manually)

To verify data consistency, run the following SQL queries in a Databricks SQL notebook or query editor:

-- Query 1: Aggregated revenue and margin by category and customer tier (top 5)
USE CATALOG retail_catalog;
SELECT 
  p.category, 
  c.tier, 
  COUNT(*) AS transaction_count, 
  ROUND(SUM(s.net), 2) AS total_revenue,
  ROUND(SUM(s.grossvalue - s.discountamount - (s.qty * p.unitcost)), 2) AS total_margin,
  CONCAT(CAST(ROUND(SUM(s.grossvalue - s.discountamount - (s.qty * p.unitcost)) / NULLIF(SUM(s.net), 0) * 100, 2) AS STRING), '%') AS margin_pct
FROM `02_silver`.silver_factsales s
INNER JOIN `02_silver`.silver_dimproduct p ON s.productid = p.productid
INNER JOIN `02_silver`.silver_dimcustomer c ON s.customerid = c.customerid
WHERE s.isreturn = 0
GROUP BY p.category, c.tier
ORDER BY transaction_count DESC
LIMIT 5;

-- Query 2: Product-level validation for specific products from vw_001
USE CATALOG retail_catalog;
SELECT 
  name AS `Product Name`, 
  ROUND(total_revenue, 2) AS `Revenue USD`,
  ROUND(total_cost, 2) AS `Cost USD`,
  ROUND(total_margin, 2) AS `Margin USD`,
  CONCAT(CAST(ROUND(margin_pct * 100, 2) AS STRING), '%') AS `Margin %`,
  rank_in_cat AS `Rank`
FROM `03_gold`.vw_001_product_category_margin
WHERE name IN (
  'Mattel Max Lego Set', 'Nerf Core Board Game Series 5',
  'Mattel Studio Cart', 'Playmobil Mini Plushie V2',
  'Playmobil Mini Action Figure Series 5'
)
ORDER BY `Revenue USD` DESC, `Product Name` ASC;

Gold Views (17)

001 vw_001_product_category_margin
002 vw_002_promo_performance
003 vw_003_customer_rfm_segments
004 vw_004_returns_analysis
005 vw_005_channel_performance
006 vw_006_seasonal_category_revenue
007 vw_007_store_performance_by_region_type
008 vw_008_pareto_margin_analysis
009 vw_009_delivery_speed_impact
010 vw_010_warranty_eco_impact
011 vw_011_hourly_sales_margin_analysis
012 vw_012_pareto_revenue_margin
013 vw_013_basket_analysis
014 vw_014_delivery_speed_impact_detailed
015 vw_015_margin_by_price_tier
016 vw_016_recency_impact_on_spend
017 vw_017_promo_margin_efficiency

Maintenance

Run the '04_optimize_delta.py' notebook periodically (e.g., weekly) to keep Delta tables compact and well-organized. This will improve query performance.

Why This Project Is Valuable

- Demonstrates end-to-end data engineering on a large scale (10M rows)
- Uses modern tools: Databricks, Delta Lake, Unity Catalog, Spark
- Implements best practices: Medallion architecture, type safety, optimization (Z-Order)
- Includes rigorous data quality validation
- Serves as a portfolio piece for job interviews or client work
- Fully reproducible with open-source scripts and clear documentation

License: MIT