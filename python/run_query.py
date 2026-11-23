import sqlite3
import sys
from pathlib import Path

import pandas as pd

root = Path(__file__).resolve().parents[1]
db_path = root / "data" / "churn.db"
query = Path(sys.argv[1]).read_text(encoding="utf-8")

with sqlite3.connect(db_path) as con:
    print(pd.read_sql_query(query, con).to_string(index=False))
