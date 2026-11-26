"""Run a SQL file against the PostgreSQL database and print the result.

Connection settings come from .env (PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD).

Usage:
    python python/run_query.py sql/02_churn_by_contract.sql
    python python/run_query.py sql/*.sql
"""

import glob
import sys
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]


def run(conn, path):
    """Return the result of a SQL file as a DataFrame."""
    with conn.cursor() as cur:
        cur.execute(Path(path).read_text(encoding="utf-8-sig"))
        columns = [col.name for col in cur.description]
        return pd.DataFrame(cur.fetchall(), columns=columns)


def main(patterns):
    # expand patterns like sql/*.sql here, because PowerShell does not
    paths = sorted(p for pattern in patterns for p in glob.glob(pattern)) or patterns
    load_dotenv(ROOT / ".env")
    with psycopg.connect() as conn:
        for path in paths:
            print(f"== {Path(path).name}")
            print(run(conn, path).to_string(index=False))
            print()


if __name__ == "__main__":
    main(sys.argv[1:])
