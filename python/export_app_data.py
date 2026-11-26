"""Export the small summary file used by the web app (app/app_data.json).

The file holds only aggregated figures and model coefficients, never
customer rows, so the dataset itself is not published with the app.

Usage:
    python python/export_app_data.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score

sys.path.insert(0, str(Path(__file__).resolve().parent))

from retention_message import CSV_PATH, FEATURES, prepare_data  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_PATH = ROOT / "app" / "app_data.json"

TENURE_LABELS = ["0-11", "12-23", "24-35", "36-47", "48-59", "60-72"]


def churn_table(df, column):
    """Customers, churned and churn rate (%) for each value of a column."""
    grouped = df.groupby(column, sort=False)["ChurnFlag"].agg(["count", "sum", "mean"])
    return [
        {"group": str(name), "customers": int(row["count"]),
         "churned": int(row["sum"]), "churn_pct": round(100 * row["mean"], 2)}
        for name, row in grouped.iterrows()
    ]


def build_summary(df):
    df = df.copy()
    df["TenureGroup"] = [TENURE_LABELS[min(t // 12, 5)] for t in df["tenure"]]

    high_risk = df[(df["Contract"] == "Month-to-month") & (df["tenure"] < 12)
                   & (df["InternetService"] == "Fiber optic")]

    train = df[df["Split"] == "Train"]
    test = df[df["Split"] == "Test"]
    logit = LogisticRegression(C=np.inf, max_iter=1000).fit(train[FEATURES], train["ChurnFlag"])
    rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=20, random_state=42)
    rf.fit(train[FEATURES], train["ChurnFlag"])

    contract_order = ["Month-to-month", "One year", "Two year"]
    by_contract = sorted(churn_table(df, "Contract"), key=lambda r: contract_order.index(r["group"]))
    by_tenure = sorted(churn_table(df, "TenureGroup"), key=lambda r: TENURE_LABELS.index(r["group"]))

    return {
        "overall": {"customers": len(df), "churned": int(df["ChurnFlag"].sum()),
                    "churn_pct": round(100 * df["ChurnFlag"].mean(), 2)},
        "by_contract": by_contract,
        "by_tenure": by_tenure,
        "high_risk": {"customers": len(high_risk), "churned": int(high_risk["ChurnFlag"].sum()),
                      "churn_pct": round(100 * high_risk["ChurnFlag"].mean(), 2)},
        "model": {
            "intercept": float(logit.intercept_[0]),
            "coefficients": dict(zip(FEATURES, map(float, logit.coef_[0]))),
            "scaling": {"tenure": 72, "MonthlyCharges": 120},
            "train_size": len(train),
            "test_size": len(test),
        },
        "auc": {
            "logistic_regression_python": round(roc_auc_score(test["ChurnFlag"], logit.predict_proba(test[FEATURES])[:, 1]), 3),
            "random_forest_5_features": round(roc_auc_score(test["ChurnFlag"], rf.predict_proba(test[FEATURES])[:, 1]), 3),
        },
    }


def main():
    summary = build_summary(prepare_data(pd.read_csv(CSV_PATH)))
    OUT_PATH.parent.mkdir(exist_ok=True)
    OUT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("Saved", OUT_PATH)


if __name__ == "__main__":
    main()