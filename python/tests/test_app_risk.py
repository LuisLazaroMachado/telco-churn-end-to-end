"""Tests for the web app's risk calculation (app/risk.py)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "app"))

from risk import churn_probability, load_app_data, risk_lines, signal_bars  # noqa: E402

DATA = load_app_data()

TOP_CUSTOMER = {
    "tenure": 3,
    "Contract": "Month-to-month",
    "InternetService": "Fiber optic",
    "PaymentMethod": "Electronic check",
    "MonthlyCharges": 107.95,
}


def test_app_data_matches_project_figures():
    assert DATA["overall"] == {"customers": 7043, "churned": 1869, "churn_pct": 26.54}
    assert [r["churn_pct"] for r in DATA["by_contract"]] == [42.71, 11.27, 2.83]
    assert DATA["high_risk"]["churn_pct"] == 70.55


def test_app_data_has_no_customer_rows():
    assert "customerID" not in Path(__file__).resolve().parents[2].joinpath("app", "app_data.json").read_text()


def test_top_customer_matches_retention_script():
    # retention_message.py --dry-run gave 0.80 for this customer (2081-VEYEH)
    assert churn_probability(TOP_CUSTOMER, DATA["model"]) == pytest.approx(0.80, abs=0.005)


def test_longer_contract_lowers_risk():
    two_year = {**TOP_CUSTOMER, "Contract": "Two year"}
    assert churn_probability(two_year, DATA["model"]) < churn_probability(TOP_CUSTOMER, DATA["model"])


def test_one_line_per_model_input():
    assert len(risk_lines(TOP_CUSTOMER, DATA["model"])) == 5


@pytest.mark.parametrize("p, bars", [(0.10, 4), (0.30, 3), (0.60, 2), (0.80, 1)])
def test_signal_bars(p, bars):
    assert signal_bars(p)[0] == bars
