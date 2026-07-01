-- View 1: SLA Compliance
CREATE OR REPLACE VIEW `my-open-project-501011.open_demo.vw_sla_compliance` AS
SELECT
  dc.region,
  fo.order_type,
  COUNT(fo.order_id)                                        AS total_orders,
  COUNTIF(fo.status = 'Completed')                         AS completed_orders,
  COUNTIF(fo.sla_breached = TRUE)                          AS sla_breached_count,
  ROUND(SAFE_DIVIDE(COUNTIF(fo.sla_breached = TRUE),
    COUNTIF(fo.status = 'Completed')) * 100, 2)            AS sla_breach_pct,
  ROUND(SAFE_DIVIDE(COUNTIF(fo.sla_breached = FALSE
    AND fo.status = 'Completed'),
    COUNTIF(fo.status = 'Completed')) * 100, 2)            AS sla_compliance_pct
FROM `my-open-project-501011.open_demo.fact_orders` fo
LEFT JOIN `my-open-project-501011.open_demo.dim_customers` dc
  ON fo.customer_id = dc.customer_id
GROUP BY dc.region, fo.order_type;


-------------
-- View 2: Engineer Fault Performance
CREATE OR REPLACE VIEW `my-open-project-501011.open_demo.vw_engineer_fault_performance` AS
SELECT
  de.engineer_name,
  de.region,
  de.team,
  COUNT(ft.ticket_id)                                      AS total_tickets,
  ROUND(AVG(ft.resolution_time_hours), 1)                  AS avg_resolution_hours,
  ROUND(MIN(ft.resolution_time_hours), 1)                  AS min_resolution_hours,
  ROUND(MAX(ft.resolution_time_hours), 1)                  AS max_resolution_hours,
  COUNTIF(ft.repeat_fault = TRUE)                          AS repeat_faults_handled
FROM `my-open-project-501011.open_demo.fact_fault_tickets` ft
LEFT JOIN `my-open-project-501011.open_demo.dim_engineers` de
  ON ft.engineer_id = de.engineer_id
GROUP BY de.engineer_name, de.region, de.team;


----------------
-- View 3: Monthly Order Trend
CREATE OR REPLACE VIEW `my-open-project-501011.open_demo.vw_monthly_order_trend` AS
SELECT
  dd.year,
  dd.month,
  dd.month_name,
  fo.order_type,
  COUNT(fo.order_id)                                       AS monthly_orders,
  SUM(COUNT(fo.order_id)) OVER (
    PARTITION BY fo.order_type
    ORDER BY dd.year, dd.month
  )                                                        AS running_total
FROM `my-open-project-501011.open_demo.fact_orders` fo
LEFT JOIN `my-open-project-501011.open_demo.dim_date` dd
  ON fo.order_date_id = dd.date_id
GROUP BY dd.year, dd.month, dd.month_name, fo.order_type;

======================

-- View 4: Engineer Visit Performance
CREATE OR REPLACE VIEW `my-open-project-501011.open_demo.vw_engineer_visit_performance` AS
SELECT
  de.engineer_name,
  de.region,
  de.team,
  COUNT(ev.visit_id)                                       AS total_visits,
  COUNTIF(ev.visit_status = 'Completed')                   AS completed_visits,
  COUNTIF(ev.visit_status = 'Missed')                      AS missed_visits,
  COUNTIF(ev.visit_status = 'Rescheduled')                 AS rescheduled_visits,
  ROUND(SAFE_DIVIDE(
    COUNTIF(ev.visit_status = 'Completed'),
    COUNT(ev.visit_id)) * 100, 2)                          AS completion_rate_pct,
  ROUND(AVG(ev.travel_time_minutes), 1)                    AS avg_travel_minutes
FROM `my-open-project-501011.open_demo.fact_engineer_visits` ev
LEFT JOIN `my-open-project-501011.open_demo.dim_engineers` de
  ON ev.engineer_id = de.engineer_id
GROUP BY de.engineer_name, de.region, de.team;


======================

-- View 5: Repeat Fault Rate
CREATE OR REPLACE VIEW `my-open-project-501011.open_demo.vw_repeat_fault_rate` AS
SELECT
  dc.region,
  dc.customer_type,
  COUNT(ft.ticket_id)                                      AS total_faults,
  COUNTIF(ft.repeat_fault = TRUE)                          AS repeat_faults,
  ROUND(SAFE_DIVIDE(
    COUNTIF(ft.repeat_fault = TRUE),
    COUNT(ft.ticket_id)) * 100, 2)                         AS repeat_fault_rate_pct,
  ROUND(AVG(ft.resolution_time_hours), 1)                  AS avg_resolution_hours
FROM `my-open-project-501011.open_demo.fact_fault_tickets` ft
LEFT JOIN `my-open-project-501011.open_demo.dim_customers` dc
  ON ft.customer_id = dc.customer_id
GROUP BY dc.region, dc.customer_type;