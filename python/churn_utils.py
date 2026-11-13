import pandas as pd


def clean_total_charges(df):
    out = df.copy()
    out["TotalCharges"] = pd.to_numeric(out["TotalCharges"], errors="coerce").fillna(0)
    return out


def add_churn_flag(df):
    out = df.copy()
    out["ChurnFlag"] = (out["Churn"] == "Yes").astype(int)
    return out


def add_model_features(df):
    out = df.copy()
    out["IsMonthToMonth"] = (out["Contract"] == "Month-to-month").astype(int)
    out["IsFiber"] = (out["InternetService"] == "Fiber optic").astype(int)
    out["IsElectronicCheck"] = (out["PaymentMethod"] == "Electronic check").astype(int)
    out["tenure_s"] = out["tenure"] / 72
    out["MonthlyCharges_s"] = out["MonthlyCharges"] / 120
    return out


def add_split(df):
    out = df.copy()
    out["Split"] = ["Test" if (i + 1) % 5 == 0 else "Train" for i in range(len(out))]
    return out