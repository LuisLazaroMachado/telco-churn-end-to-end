"""Cleaning and feature helpers shared by the notebook, Phase 5 and the tests.

Each function returns a copy and leaves the input DataFrame unchanged.
"""

import pandas as pd


def clean_total_charges(df):
    """Convert TotalCharges to numbers; the 11 blanks (tenure = 0) become 0."""
    out = df.copy()
    out["TotalCharges"] = pd.to_numeric(out["TotalCharges"], errors="coerce").fillna(0)
    return out


def add_churn_flag(df):
    """Add ChurnFlag: 1 if the customer left (Churn = "Yes"), otherwise 0."""
    out = df.copy()
    out["ChurnFlag"] = (out["Churn"] == "Yes").astype(int)
    return out


def add_model_features(df):
    """Add the 5 model features used in Excel: 3 indicators and 2 scaled numbers.

    tenure is divided by 72 and MonthlyCharges by 120, so both are on a 0-1 scale.
    """
    out = df.copy()
    out["IsMonthToMonth"] = (out["Contract"] == "Month-to-month").astype(int)
    out["IsFiber"] = (out["InternetService"] == "Fiber optic").astype(int)
    out["IsElectronicCheck"] = (out["PaymentMethod"] == "Electronic check").astype(int)
    out["tenure_s"] = out["tenure"] / 72
    out["MonthlyCharges_s"] = out["MonthlyCharges"] / 120
    return out


def add_split(df):
    """Mark every 5th row as Test and the rest as Train, the same rule as Excel."""
    out = df.copy()
    out["Split"] = ["Test" if (i + 1) % 5 == 0 else "Train" for i in range(len(out))]
    return out