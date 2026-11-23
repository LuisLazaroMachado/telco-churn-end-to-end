import sqlite3
from pathlib import Path

import pandas as pd

root = Path(__file__).resolve().parents[1]
csv_path = root / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"
db_path = root / "data" / "churn.db"

df = pd.read_csv(csv_path)

with sqlite3.connect(db_path) as con:
    df.to_sql("customers", con, if_exists="replace", index=False)

print("Loaded", len(df), "rows into", db_path)
