"""Create the PostgreSQL schema (sql/schema.sql) and load the Telco CSV into it.

Connection settings come from .env (standard PostgreSQL variables):
    PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD

Usage:
    python python/load_to_postgres.py
"""

import sys
from pathlib import Path

import pandas as pd
import psycopg

sys.path.insert(0, str(Path(__file__).resolve().parent))

from churn_utils import clean_total_charges  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
SCHEMA_PATH = ROOT / "sql" / "schema.sql"

CONTRACT_IDS = {"Month-to-month": 1, "One year": 2, "Two year": 3}
PAYMENT_IDS = {
    "Electronic check": 1,
    "Mailed check": 2,
    "Bank transfer (automatic)": 3,
    "Credit card (automatic)": 4,
}


def yes_no(value):
    """'Yes' -> True, 'No' -> False, 'No internet/phone service' -> None."""
    return {"Yes": True, "No": False}.get(value)


def build_rows(raw):
    """Split the flat CSV into rows for the customers, accounts and services tables."""
    df = clean_total_charges(raw)
    customers, accounts, services = [], [], []
    for r in df.itertuples(index=False):
        customers.append((r.customerID, r.gender, bool(r.SeniorCitizen), yes_no(r.Partner), yes_no(r.Dependents)))
        accounts.append((
            r.customerID, int(r.tenure), CONTRACT_IDS[r.Contract], PAYMENT_IDS[r.PaymentMethod],
            yes_no(r.PaperlessBilling), float(r.MonthlyCharges), float(r.TotalCharges), yes_no(r.Churn),
        ))
        services.append((
            r.customerID, yes_no(r.PhoneService), yes_no(r.MultipleLines), r.InternetService,
            yes_no(r.OnlineSecurity), yes_no(r.OnlineBackup), yes_no(r.DeviceProtection),
            yes_no(r.TechSupport), yes_no(r.StreamingTV), yes_no(r.StreamingMovies),
        ))
    return customers, accounts, services


def load(conn, raw):
    """Recreate the schema and insert all rows in one transaction."""
    customers, accounts, services = build_rows(raw)
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(SCHEMA_PATH.read_text(encoding="utf-8"))
        cur.executemany("INSERT INTO customers VALUES (%s, %s, %s, %s, %s)", customers)
        cur.executemany("INSERT INTO accounts VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", accounts)
        cur.executemany("INSERT INTO services VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", services)
    return len(customers)


def main():
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
    with psycopg.connect() as conn:  # reads the PG* variables
        count = load(conn, pd.read_csv(CSV_PATH))
    print(f"Loaded {count} customers into PostgreSQL")


if __name__ == "__main__":
    main()
