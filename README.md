# Telecom Network Operations Analytics
### Google BigQuery | Python | Power BI

A end-to-end Business Intelligence project modelling telecom network operations
data inspired by real-world provisioning and fault management workflows
(similar to BT Openreach network operations).

---

## Project Overview

This project simulates a telecom network operations data warehouse covering:
- Customer provisioning orders (New Connection / Repair / Upgrade)
- Network fault tickets and resolution tracking
- Engineer visit scheduling and performance
- SLA compliance monitoring across UK regions

---

## Architecture

```
Python (Data Generation)
        |
        v
Google BigQuery (Data Warehouse)
        |
   [Star Schema]
        |
   Dim Tables          Fact Tables
   ----------          -----------
   dim_customers  -->  fact_orders
   dim_engineers  -->  fact_fault_tickets
   dim_exchanges  -->  fact_engineer_visits
   dim_date
        |
        v
   BigQuery Views (Semantic Layer)
        |
        v
   Power BI Dashboard
```

---

## Star Schema Design

### Dimension Tables
| Table | Description | Rows |
|---|---|---|
| dim_customers | Customer details, region, type | 500 |
| dim_engineers | Engineer details, team, experience | 30 |
| dim_exchanges | Network exchange locations | 15 |
| dim_date | Full date dimension 2024-2025 | 731 |

### Fact Tables
| Table | Description | Rows |
|---|---|---|
| fact_orders | Provisioning/repair orders with SLA tracking | 3,000 |
| fact_fault_tickets | Network fault tickets and resolution time | 1,500 |
| fact_engineer_visits | Engineer visit scheduling and outcomes | 4,000 |

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Google BigQuery | Cloud data warehouse |
| Python 3 | Synthetic data generation and loading |
| Faker library | Realistic UK telecom data generation |
| pandas | Data manipulation and DataFrame creation |
| google-cloud-bigquery | BigQuery Python client |
| Power BI Desktop | Dashboard and visualisation |
| SQL | Transformations, views, analysis |

---

## BigQuery Views (Semantic Layer)

Five analytical views built on top of the star schema:

| View | Business Question Answered |
|---|---|
| vw_sla_compliance | SLA compliance % by region and order type |
| vw_engineer_fault_performance | Average resolution time and repeat faults by engineer |
| vw_monthly_order_trend | Monthly order volumes with running totals |
| vw_engineer_visit_performance | Visit completion rate and travel time by engineer |
| vw_repeat_fault_rate | Repeat fault rate % by region and customer type |

---

## Key SQL Concepts Used

```sql
-- SAFE_DIVIDE: avoids divide by zero (BigQuery equivalent of Oracle NULLIF)
ROUND(SAFE_DIVIDE(COUNTIF(sla_breached = TRUE), COUNT(order_id)) * 100, 2)

-- COUNTIF: cleaner than Oracle SUM(CASE WHEN condition THEN 1 ELSE 0 END)
COUNTIF(visit_status = 'Completed')

-- Window Functions: running totals by order type
SUM(COUNT(order_id)) OVER (
  PARTITION BY order_type
  ORDER BY year, month
)

-- INFORMATION_SCHEMA: schema validation (equivalent to Oracle DESC)
SELECT column_name, data_type
FROM openreach_demo.INFORMATION_SCHEMA.COLUMNS
WHERE table_name = 'fact_orders'
```

---

## Power BI Dashboard

Three dashboard pages built in Power BI Desktop connected to BigQuery:

### Page 1 — SLA Performance Overview
- KPI Cards: Total Orders, SLA Breaches, Avg Breach Rate
- Bar Chart: SLA Compliance % by Region
- Column Chart: Orders by Type vs SLA Breaches
- Slicer: Filter by Region

### Page 2 — Engineer Performance
- Scorecard Table: Engineer tickets, resolution time, repeat faults
- Bar Chart: Visit completion rate by engineer
- Slicer: Filter by Team

### Page 3 — Fault Analysis
- Line Chart: Monthly order trend by type (2024-2025)
- Bar Chart: Repeat fault rate % by region
- Column Chart: Total faults by customer type
- Slicer: Filter by Customer Type

---

## Oracle to BigQuery Migration Notes

Key differences encountered (from real migration experience):

| Oracle | BigQuery |
|---|---|
| VARCHAR2 | STRING |
| NUMBER | INT64 / FLOAT64 |
| DATE (includes time) | DATE or TIMESTAMP |
| NVL() | IFNULL() or COALESCE() |
| DECODE() | CASE WHEN |
| TO_CHAR(date,'YYYY-MM') | FORMAT_DATE('%Y-%m', date) |
| SYSDATE | CURRENT_DATE() |
| ROWNUM | ROW_NUMBER() OVER() |
| Stored Procedures / PL/SQL | BigQuery Scripting or Python |
| Sequences / Triggers | Generated in Python / application layer |
| DESC tablename | INFORMATION_SCHEMA.COLUMNS |
| CONNECT BY (hierarchical) | Recursive CTEs |

---

## How to Run

### Prerequisites
- Google Cloud account with BigQuery enabled
- Python 3.8+
- Power BI Desktop

### Steps
```bash
# 1. Install dependencies
pip install google-cloud-bigquery faker pandas pyarrow db-dtypes pandas-gbq

# 2. Set up Google Cloud service account and download JSON key

# 3. Update config in generate_data.py
PROJECT_ID = "your-project-id"
KEY_PATH = "path/to/your-key.json"

# 4. Run data generation
python generate_data.py

# 5. Run SQL views in BigQuery console (see /sql/views.sql)

# 6. Open Power BI → Get Data → Google BigQuery → connect to views
```

---

## Project Insights (Sample Findings)

- North East region has the highest SLA breach rate across all order types
- Residential customers account for ~80% of total fault tickets
- Repair orders have the highest SLA compliance compared to New Connections
- Average engineer fault resolution time is approximately 35 hours
- ~20% of completed orders breach SLA targets

---

## Author

Michael Johnson  
8+ years PL/SQL and Oracle Database experience  
Transitioning to BI Engineering with Google BigQuery and Power BI  
[LinkedIn Profile] | [Email]
