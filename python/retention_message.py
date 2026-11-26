"""Generate personalised retention messages for high-risk customers with an LLM.

The logistic regression from Phase 2 scores the test customers who have not
churned yet. The customers with the highest churn probability get a short
retention message written by an LLM, in English or Spanish.

The provider is set in .env (any OpenAI-compatible endpoint):
    LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

Usage:
    python python/retention_message.py --dry-run           # no API call
    python python/retention_message.py --n 3 --lang es
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))

from churn_utils import (  # noqa: E402
    add_churn_flag,
    add_model_features,
    add_split,
    clean_total_charges,
)

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "raw" / "WA_Fn-UseC_-Telco-Customer-Churn.csv"

FEATURES = ["tenure_s", "MonthlyCharges_s", "IsMonthToMonth", "IsFiber", "IsElectronicCheck"]

# Hard limit per run, to protect the API quota.
MAX_CUSTOMERS = 5

LANGUAGES = {"en": "English", "es": "Spanish"}

# Only these fields are sent to the LLM. No customerID or personal data.
PROFILE_FIELDS = [
    "tenure",
    "Contract",
    "InternetService",
    "OnlineSecurity",
    "TechSupport",
    "PaymentMethod",
    "MonthlyCharges",
]

# The LLM may only choose from these offers, so it cannot promise
# discounts or prices that do not exist.
OFFERS = [
    "a discount for switching to a one-year or two-year contract",
    "a free trial of online security",
    "a free trial of tech support",
    "a bill reminder service when switching to automatic payment",
]


def prepare_data(raw):
    """Apply the same cleaning and features used in Excel and the notebook."""
    df = clean_total_charges(raw)
    df = add_churn_flag(df)
    df = add_model_features(df)
    return add_split(df)


def score_active_customers(df):
    """Train on the train split and score test customers who have not churned.

    Returns those customers sorted by churn probability, highest first.
    """
    train = df[df["Split"] == "Train"]
    model = LogisticRegression(C=np.inf, max_iter=1000)
    model.fit(train[FEATURES], train["ChurnFlag"])

    active = df[(df["Split"] == "Test") & (df["ChurnFlag"] == 0)].copy()
    active["churn_probability"] = model.predict_proba(active[FEATURES])[:, 1]
    return active.sort_values("churn_probability", ascending=False)


def build_profile(row):
    """Keep only the fields the LLM needs."""
    return {field: row[field] for field in PROFILE_FIELDS}


def build_messages(profile, lang="en"):
    """Build the chat messages (system + user) for one customer."""
    if lang not in LANGUAGES:
        raise ValueError(f"lang must be one of {sorted(LANGUAGES)}, got {lang!r}")

    offers = "\n".join(f"- {offer}" for offer in OFFERS)
    system = (
        "You are a customer retention specialist at a telecom company. "
        f"Write a short, friendly message to a customer in {LANGUAGES[lang]}, "
        "at most 80 words. Choose the ONE offer below that best fits the "
        "customer profile:\n"
        f"{offers}\n"
        "Rules: do not mention prices, percentages or amounts; do not mention "
        "that the customer might leave or that a model predicted it; do not "
        "invent offers. Return only the message text."
    )
    details = "\n".join(f"- {key}: {value}" for key, value in profile.items())
    user = f"Customer profile:\n{details}"
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def make_client():
    """Create an OpenAI-compatible client from environment variables."""
    from openai import OpenAI

    missing = [name for name in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL") if not os.getenv(name)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)} (see .env)")
    return OpenAI(api_key=os.environ["LLM_API_KEY"], base_url=os.environ["LLM_BASE_URL"])


def generate_message(client, model, messages):
    """Send one request to the LLM and return the message text."""
    response = client.chat.completions.create(model=model, messages=messages, temperature=0.7)
    return response.choices[0].message.content.strip()


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--n", type=int, default=3, help=f"customers to contact (1-{MAX_CUSTOMERS})")
    parser.add_argument("--lang", choices=sorted(LANGUAGES), default="en")
    parser.add_argument("--dry-run", action="store_true", help="print the prompts without calling the API")
    args = parser.parse_args(argv)
    args.n = max(1, min(args.n, MAX_CUSTOMERS))
    return args


def main(argv=None):
    args = parse_args(argv)
    scored = score_active_customers(prepare_data(pd.read_csv(CSV_PATH)))
    top = scored.head(args.n)

    client = model = None
    if not args.dry_run:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
        client = make_client()
        model = os.environ["LLM_MODEL"]

    for _, row in top.iterrows():
        messages = build_messages(build_profile(row), args.lang)
        print(f"=== {row['customerID']} (churn probability {row['churn_probability']:.2f})")
        if args.dry_run:
            print(messages[1]["content"])
        else:
            print(generate_message(client, model, messages))
        print()


if __name__ == "__main__":
    main()
