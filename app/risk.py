"""Risk calculation for the web app, using the exported logistic regression.

Kept separate from the Streamlit page so it can be tested without a browser.
"""

import json
import math
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent / "app_data.json"


def load_app_data(path=DATA_PATH):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def risk_lines(profile, model):
    """Return one (label, value, effect) line per model input.

    The effect is that input's contribution to the risk score (log-odds):
    positive pushes the churn probability up, negative pushes it down.
    """
    coef = model["coefficients"]
    scale = model["scaling"]
    return [
        ("Tenure", f"{profile['tenure']} months",
         coef["tenure_s"] * profile["tenure"] / scale["tenure"]),
        ("Contract", profile["Contract"],
         coef["IsMonthToMonth"] * (profile["Contract"] == "Month-to-month")),
        ("Internet", profile["InternetService"],
         coef["IsFiber"] * (profile["InternetService"] == "Fiber optic")),
        ("Payment", profile["PaymentMethod"],
         coef["IsElectronicCheck"] * (profile["PaymentMethod"] == "Electronic check")),
        ("Monthly charges", f"{profile['MonthlyCharges']:.2f}",
         coef["MonthlyCharges_s"] * profile["MonthlyCharges"] / scale["MonthlyCharges"]),
    ]


def churn_probability(profile, model):
    """Logistic regression probability: 1 / (1 + e^-(intercept + effects))."""
    score = model["intercept"] + sum(effect for _, _, effect in risk_lines(profile, model))
    return 1 / (1 + math.exp(-score))


def signal_bars(probability):
    """Phone-style signal bars (4 = strong relationship, 1 = about to drop)."""
    if probability < 0.25:
        return 4, "Strong"
    if probability < 0.50:
        return 3, "Fair"
    if probability < 0.75:
        return 2, "Weak"
    return 1, "About to drop"
