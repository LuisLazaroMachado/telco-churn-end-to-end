import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from churn_utils import (
    add_churn_flag,
    add_model_features,
    add_split,
    clean_total_charges,
)


def test_blank_total_charges_become_zero():
    df = pd.DataFrame({"TotalCharges": ["29.85", " ", "108.15"]})
    result = clean_total_charges(df)
    assert result["TotalCharges"].tolist() == [29.85, 0.0, 108.15]


def test_churn_flag_is_binary():
    df = pd.DataFrame({"Churn": ["Yes", "No", "Yes"]})
    result = add_churn_flag(df)
    assert result["ChurnFlag"].tolist() == [1, 0, 1]


def test_model_features_and_scaling():
    df = pd.DataFrame({
        "Contract": ["Month-to-month", "Two year"],
        "InternetService": ["Fiber optic", "DSL"],
        "PaymentMethod": ["Electronic check", "Mailed check"],
        "tenure": [72, 36],
        "MonthlyCharges": [120.0, 60.0],
    })
    result = add_model_features(df)
    assert result["IsMonthToMonth"].tolist() == [1, 0]
    assert result["IsFiber"].tolist() == [1, 0]
    assert result["IsElectronicCheck"].tolist() == [1, 0]
    assert result["tenure_s"].tolist() == [1.0, 0.5]
    assert result["MonthlyCharges_s"].tolist() == [1.0, 0.5]


def test_split_matches_excel_rule():
    df = pd.DataFrame({"x": range(10)})
    result = add_split(df)
    assert (result["Split"] == "Test").sum() == 2
    assert result.loc[4, "Split"] == "Test"
    assert result.loc[9, "Split"] == "Test"