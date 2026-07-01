"""
generate_data.py
Generates synthetic Openreach-style telecom data and loads it into BigQuery.

BEFORE RUNNING:
1. pip install google-cloud-bigquery faker pandas pyarrow db-dtypes
2. Update PROJECT_ID and KEY_PATH below
3. Make sure the 7 tables already exist in BigQuery (Step 2)
"""

import random
from datetime import datetime, timedelta
import pandas as pd
from faker import Faker
from google.cloud import bigquery
from google.oauth2 import service_account

# ---------- CONFIG ----------
PROJECT_ID = "my-open-project-501011"          # <-- change this
DATASET_ID = "open_demo"
KEY_PATH = r"C:\Users\micha\Downloads\my-open-project-501011-80bb2eb217e5.json"
# <-- change this

NUM_CUSTOMERS = 500
NUM_ENGINEERS = 30
NUM_EXCHANGES = 15
NUM_ORDERS = 3000
NUM_TICKETS = 1500
NUM_VISITS = 4000

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2025, 12, 31)

fake = Faker("en_GB")
random.seed(42)

REGIONS = ["London", "South East", "South West", "Midlands", "North West", "North East", "Scotland", "Wales"]
ORDER_TYPES = ["New Connection", "Repair", "Upgrade"]
ORDER_STATUS = ["Completed", "Pending", "Cancelled"]
FAULT_TYPES = ["Line Fault", "No Dial Tone", "Slow Speed", "Intermittent Connection", "No Broadband Signal"]
VISIT_STATUS = ["Completed", "Missed", "Rescheduled", "Cancelled"]
APPOINTMENT_SLOTS = ["AM", "PM", "All Day"]
VISIT_OUTCOMES = ["Fixed", "Parts Needed", "Customer No Show", "Access Issue"]
CUSTOMER_TYPES = ["Residential", "Business"]


def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def date_id(dt):
    return int(dt.strftime("%Y%m%d"))


# ---------- DIM: DATE ----------
def generate_dim_date():
    rows = []
    current = START_DATE
    while current <= END_DATE:
        rows.append({
            "date_id": date_id(current),
            "full_date": current.date(),
            "day": current.day,
            "month": current.month,
            "month_name": current.strftime("%B"),
            "quarter": (current.month - 1) // 3 + 1,
            "year": current.year,
            "day_of_week": current.strftime("%A"),
            "is_weekend": current.weekday() >= 5,
        })
        current += timedelta(days=1)
    return pd.DataFrame(rows)


# ---------- DIM: CUSTOMERS ----------
def generate_dim_customers():
    rows = []
    for i in range(1, NUM_CUSTOMERS + 1):
        rows.append({
            "customer_id": f"CUST{i:05d}",
            "customer_name": fake.name(),
            "region": random.choice(REGIONS),
            "postcode": fake.postcode(),
            "customer_type": random.choices(CUSTOMER_TYPES, weights=[0.8, 0.2])[0],
        })
    return pd.DataFrame(rows)


# ---------- DIM: ENGINEERS ----------
def generate_dim_engineers():
    rows = []
    for i in range(1, NUM_ENGINEERS + 1):
        rows.append({
            "engineer_id": f"ENG{i:04d}",
            "engineer_name": fake.name(),
            "region": random.choice(REGIONS),
            "team": random.choice(["Provisioning", "Repair", "Field Ops"]),
            "experience_years": random.randint(1, 20),
        })
    return pd.DataFrame(rows)


# ---------- DIM: EXCHANGES ----------
def generate_dim_exchanges():
    rows = []
    for i in range(1, NUM_EXCHANGES + 1):
        region = random.choice(REGIONS)
        rows.append({
            "exchange_id": f"EXC{i:03d}",
            "exchange_name": f"{fake.city()} Exchange",
            "region": region,
            "city": fake.city(),
        })
    return pd.DataFrame(rows)


# ---------- FACT: ORDERS ----------
def generate_fact_orders(customer_ids, engineer_ids, exchange_ids):
    rows = []
    for i in range(1, NUM_ORDERS + 1):
        order_date = random_date(START_DATE, END_DATE)
        order_type = random.choice(ORDER_TYPES)
        status = random.choices(ORDER_STATUS, weights=[0.75, 0.15, 0.10])[0]
        sla_target = random.choice([1, 2, 3, 5, 7])
        # Completion days: sometimes breaches SLA
        if random.random() < 0.2:
            actual_days = sla_target + random.randint(1, 5)  # breach
        else:
            actual_days = max(1, sla_target - random.randint(0, 1))
        sla_breached = actual_days > sla_target if status == "Completed" else False

        rows.append({
            "order_id": f"ORD{i:06d}",
            "customer_id": random.choice(customer_ids),
            "exchange_id": random.choice(exchange_ids),
            "engineer_id": random.choice(engineer_ids),
            "order_date_id": date_id(order_date),
            "order_type": order_type,
            "status": status,
            "sla_target_days": sla_target,
            "actual_completion_days": actual_days if status == "Completed" else None,
            "sla_breached": sla_breached,
        })
    return pd.DataFrame(rows)


# ---------- FACT: FAULT TICKETS ----------
def generate_fact_fault_tickets(customer_ids, engineer_ids, exchange_ids):
    rows = []
    customer_fault_count = {}
    for i in range(1, NUM_TICKETS + 1):
        reported_date = random_date(START_DATE, END_DATE)
        resolve_hours = round(random.uniform(1, 72), 1)
        resolved_date = reported_date + timedelta(hours=resolve_hours)
        cust = random.choice(customer_ids)

        customer_fault_count[cust] = customer_fault_count.get(cust, 0) + 1
        repeat = customer_fault_count[cust] > 1 and random.random() < 0.3

        rows.append({
            "ticket_id": f"TCK{i:06d}",
            "customer_id": cust,
            "exchange_id": random.choice(exchange_ids),
            "engineer_id": random.choice(engineer_ids),
            "reported_date_id": date_id(reported_date),
            "resolved_date_id": date_id(resolved_date),
            "fault_type": random.choice(FAULT_TYPES),
            "resolution_time_hours": resolve_hours,
            "repeat_fault": repeat,
        })
    return pd.DataFrame(rows)


# ---------- FACT: ENGINEER VISITS ----------
def generate_fact_engineer_visits(order_ids, ticket_ids, engineer_ids):
    rows = []
    for i in range(1, NUM_VISITS + 1):
        link_to_order = random.random() < 0.55
        visit_date = random_date(START_DATE, END_DATE)
        rows.append({
            "visit_id": f"VIS{i:06d}",
            "order_id": random.choice(order_ids) if link_to_order else None,
            "ticket_id": None if link_to_order else random.choice(ticket_ids),
            "engineer_id": random.choice(engineer_ids),
            "scheduled_date_id": date_id(visit_date),
            "visit_status": random.choices(VISIT_STATUS, weights=[0.7, 0.1, 0.15, 0.05])[0],
            "appointment_slot": random.choice(APPOINTMENT_SLOTS),
            "travel_time_minutes": random.randint(5, 90),
            "visit_outcome": random.choice(VISIT_OUTCOMES),
        })
    return pd.DataFrame(rows)


# ---------- LOAD TO BIGQUERY ----------
def load_to_bigquery(df, table_name, client):
    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"
    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()  # wait for completion
    print(f"Loaded {len(df)} rows into {table_id}")


def main():
    credentials = service_account.Credentials.from_service_account_file(KEY_PATH)
    client = bigquery.Client(project=PROJECT_ID, credentials=credentials)

    print("Generating dimension tables...")
    dim_date = generate_dim_date()
    dim_customers = generate_dim_customers()
    dim_engineers = generate_dim_engineers()
    dim_exchanges = generate_dim_exchanges()

    print("Generating fact tables...")
    fact_orders = generate_fact_orders(
        dim_customers["customer_id"].tolist(),
        dim_engineers["engineer_id"].tolist(),
        dim_exchanges["exchange_id"].tolist(),
    )
    fact_fault_tickets = generate_fact_fault_tickets(
        dim_customers["customer_id"].tolist(),
        dim_engineers["engineer_id"].tolist(),
        dim_exchanges["exchange_id"].tolist(),
    )
    fact_engineer_visits = generate_fact_engineer_visits(
        fact_orders["order_id"].tolist(),
        fact_fault_tickets["ticket_id"].tolist(),
        dim_engineers["engineer_id"].tolist(),
    )

    print("Loading to BigQuery...")
    load_to_bigquery(dim_date, "dim_date", client)
    load_to_bigquery(dim_customers, "dim_customers", client)
    load_to_bigquery(dim_engineers, "dim_engineers", client)
    load_to_bigquery(dim_exchanges, "dim_exchanges", client)
    load_to_bigquery(fact_orders, "fact_orders", client)
    load_to_bigquery(fact_fault_tickets, "fact_fault_tickets", client)
    load_to_bigquery(fact_engineer_visits, "fact_engineer_visits", client)

    print("\nAll done! Go check your BigQuery tables.")


if __name__ == "__main__":
    main()