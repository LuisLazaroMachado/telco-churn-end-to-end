"""Tests for retention_message.py. The LLM is replaced by a fake client,
so these tests never call the API."""

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from retention_message import (  # noqa: E402
    MAX_CUSTOMERS,
    build_messages,
    build_profile,
    generate_message,
    make_client,
    parse_args,
    prepare_data,
    score_active_customers,
)


def fake_raw(n=100, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "customerID": [f"C{i:03d}" for i in range(n)],
        "tenure": rng.integers(0, 73, n),
        "Contract": rng.choice(["Month-to-month", "One year", "Two year"], n),
        "InternetService": rng.choice(["Fiber optic", "DSL", "No"], n),
        "OnlineSecurity": rng.choice(["Yes", "No"], n),
        "TechSupport": rng.choice(["Yes", "No"], n),
        "PaymentMethod": rng.choice(["Electronic check", "Mailed check"], n),
        "MonthlyCharges": rng.uniform(20, 118, n).round(2),
        "TotalCharges": ["100.0"] * (n - 1) + [" "],
        "Churn": rng.choice(["Yes", "No"], n),
    })


class FakeClient:
    """Mimics client.chat.completions.create and records the call."""

    def __init__(self, text):
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))
        self._text = text

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=self._text)
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_scoring_keeps_only_active_test_customers_sorted():
    scored = score_active_customers(prepare_data(fake_raw()))
    assert (scored["Split"] == "Test").all()
    assert (scored["ChurnFlag"] == 0).all()
    assert scored["churn_probability"].is_monotonic_decreasing


def test_profile_excludes_customer_id():
    row = prepare_data(fake_raw()).iloc[0]
    profile = build_profile(row)
    assert "customerID" not in profile
    assert profile["Contract"] == row["Contract"]


@pytest.mark.parametrize("lang, name", [("en", "English"), ("es", "Spanish")])
def test_messages_use_requested_language(lang, name):
    messages = build_messages({"tenure": 2}, lang)
    assert [m["role"] for m in messages] == ["system", "user"]
    assert name in messages[0]["content"]
    assert "tenure: 2" in messages[1]["content"]


def test_unknown_language_is_rejected():
    with pytest.raises(ValueError):
        build_messages({"tenure": 2}, "fr")


def test_generate_message_uses_fake_client():
    client = FakeClient("  Hello, we have an offer for you.  ")
    messages = build_messages({"tenure": 2})
    text = generate_message(client, "test-model", messages)
    assert text == "Hello, we have an offer for you."
    assert client.calls[0]["model"] == "test-model"
    assert client.calls[0]["messages"] == messages


def test_missing_settings_raise_clear_error(monkeypatch):
    for name in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL"):
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        make_client()


def test_customer_count_is_capped():
    assert parse_args(["--n", "50"]).n == MAX_CUSTOMERS
    assert parse_args(["--n", "0"]).n == 1
