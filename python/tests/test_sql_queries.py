"""Tests for the PostgreSQL schema, loader and queries.

Two groups:
- Logic tests load made-up data into a temporary schema and check the SQL
  results against the same calculation in pandas. They run anywhere a
  PostgreSQL server is available (locally and in GitHub Actions).
- Official-figure tests check the real loaded data and are skipped when it
  is not there (for example in GitHub Actions, which has no CSV).

All tests are skipped if no PostgreSQL connection is configured.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

psycopg = pytest.importorskip("psycopg")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))

from load_to_postgres import load  # noqa: E402
from run_query import run  # noqa: E402

SQL = ROOT / "sql"
TEST_SCHEMA = "pytest_telco"


def fake_raw(n=3000, seed=1):
    """Made-up customers in the same format as the IBM Telco CSV."""
    rng = np.random.default_rng(seed)
    internet = rng.choice(["DSL", "Fiber optic", "No"], n)
    phone = rng.choice(["Yes", "No"], n)
    tenure = rng.integers(0, 73, n)

    def addon():
        return np.where(internet == "No", "No internet service", rng.choice(["Yes", "No"], n))

    return pd.DataFrame({
        "customerID": [f"{i:04d}-TEST" for i in range(n)],
        "gender": rng.choice(["Female", "Male"], n),
        "SeniorCitizen": rng.integers(0, 2, n),
        "Partner": rng.choice(["Yes", "No"], n),
        "Dependents": rng.choice(["Yes", "No"], n),
        "tenure": tenure,
        "PhoneService": phone,
        "MultipleLines": np.where(phone == "No", "No phone service", rng.choice(["Yes", "No"], n)),
        "InternetService": internet,
        "OnlineSecurity": addon(),
        "OnlineBackup": addon(),
        "DeviceProtection": addon(),
        "TechSupport": addon(),
        "StreamingTV": addon(),
        "StreamingMovies": addon(),
        "Contract": rng.choice(["Month-to-month", "One year", "Two year"], n),
        "PaperlessBilling": rng.choice(["Yes", "No"], n),
        "PaymentMethod": rng.choice(
            ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"], n),
        "MonthlyCharges": rng.uniform(18.25, 118.75, n).round(2),
        "TotalCharges": np.where(tenure == 0, " ", rng.uniform(18, 8000, n).round(2).astype(str)),
        "Churn": rng.choice(["Yes", "No"], n),
    })


def connect():
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    try:
        return psycopg.connect(connect_timeout=3)
    except psycopg.OperationalError:
        pytest.skip("no PostgreSQL connection configured")


@pytest.fixture(scope="module")
def fake_db():
    """Load made-up data into a temporary schema; the real tables are not touched."""
    raw = fake_raw()
    conn = connect()
    conn.execute(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE")
    conn.execute(f"CREATE SCHEMA {TEST_SCHEMA}")
    conn.execute(f"SET search_path TO {TEST_SCHEMA}")
    load(conn, raw)
    yield conn, raw
    conn.execute(f"DROP SCHEMA {TEST_SCHEMA} CASCADE")
    conn.commit()
    conn.close()


def pct(series):
    return round(100 * series.mean(), 2)


def test_every_query_runs(fake_db):
    conn, _ = fake_db
    for path in sorted(SQL.glob("0*.sql")):
        assert len(run(conn, path)) > 0, path.name


def test_data_checks_count_all_rows(fake_db):
    conn, raw = fake_db
    result = dict(run(conn, SQL / "01_data_checks.sql").values)
    assert result["customers"] == result["accounts"] == result["services"] == str(len(raw))
    assert result["customers without an account"] == "0"


def test_churn_by_contract_matches_pandas(fake_db):
    conn, raw = fake_db
    sql = run(conn, SQL / "02_churn_by_contract.sql").set_index("contract")["churn_pct"].astype(float)
    churned = raw["Churn"] == "Yes"
    for contract, value in sql.items():
        assert value == pct(churned[raw["Contract"] == contract])


def test_highest_risk_group_matches_pandas(fake_db):
    conn, raw = fake_db
    row = run(conn, SQL / "04_highest_risk_group.sql").iloc[0]
    group = raw[(raw["Contract"] == "Month-to-month") & (raw["tenure"] < 12)
                & (raw["InternetService"] == "Fiber optic")]
    assert row["customers"] == len(group)
    assert float(row["churn_pct"]) == pct(group["Churn"] == "Yes")


def test_cumulative_churn_ends_at_100(fake_db):
    conn, _ = fake_db
    result = run(conn, SQL / "03_churn_by_tenure.sql")
    assert float(result["cumulative_share_of_churn_pct"].iloc[-1]) == 100.0
    assert result["cumulative_share_of_churn_pct"].astype(float).is_monotonic_increasing


def test_schema_rejects_impossible_values(fake_db):
    conn, _ = fake_db
    with pytest.raises(psycopg.errors.CheckViolation):
        with conn.transaction():
            conn.execute("UPDATE accounts SET tenure_months = -1 WHERE customer_id = '0000-TEST'")


@pytest.fixture(scope="module")
def real_db():
    conn = connect()
    exists = conn.execute("SELECT to_regclass('public.accounts')").fetchone()[0]
    if not exists or conn.execute("SELECT COUNT(*) FROM public.accounts").fetchone()[0] != 7043:
        conn.close()
        pytest.skip("real Telco data not loaded")
    conn.execute("SET search_path TO public")
    yield conn
    conn.close()


def test_official_figures(real_db):
    contract = run(real_db, SQL / "02_churn_by_contract.sql")
    assert contract["churn_pct"].astype(float).tolist() == [42.71, 11.27, 2.83]

    tenure = run(real_db, SQL / "03_churn_by_tenure.sql").set_index("tenure_months")["churn_pct"].astype(float)
    assert (tenure["0-11"], tenure["60-72"]) == (48.28, 6.68)

    risk = run(real_db, SQL / "04_highest_risk_group.sql").iloc[0]
    assert (risk["customers"], risk["churned"], float(risk["churn_pct"])) == (876, 618, 70.55)

    matrix = run(real_db, SQL / "05_contract_tenure_matrix.sql").set_index("contract")
    assert float(matrix.loc["Month-to-month", "0-11"]) == 51.94
