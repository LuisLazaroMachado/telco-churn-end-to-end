"""Telco churn risk: web app for the telco-churn-end-to-end project.

Run locally from the project root:
    streamlit run app/streamlit_app.py
"""

import html
import os
import sys
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
ROOT = APP_DIR.parent
sys.path.insert(0, str(APP_DIR))
sys.path.insert(0, str(ROOT / "python"))

from risk import churn_probability, load_app_data, risk_lines, signal_bars  # noqa: E402
from retention_message import build_messages, generate_message  # noqa: E402

REPO_URL = "https://github.com/LuisLazaroMachado/telco-churn-end-to-end"
MESSAGES_PER_VISIT = 3

# Real output from python/retention_message.py, shown when the API is unavailable.
SAVED_EXAMPLE = (
    "Hi there! We hope you are enjoying your fiber optic internet experience. As a "
    "valued customer, we would love to help you save on your service. You are eligible "
    "to receive a discount simply by switching your plan to a one-year or two-year "
    "contract. It is a fantastic way to enjoy peace of mind and uninterrupted "
    "connectivity. Reach out to our friendly support team today to update your account "
    "and take advantage of this offer!"
)

INK = "#14213D"
RULE = "#A9B4BF"
GREEN = "#3F8F6B"
AMBER = "#E0A030"
RED = "#C2453A"

st.set_page_config(page_title="Telco churn risk", page_icon="📶", layout="wide")

st.markdown(
    f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap');

.stApp :is(h1, h2, h3, h4, p, li, label, input, button, textarea, div, span):not([data-testid="stIconMaterial"]) {{
  font-family: 'IBM Plex Sans', sans-serif !important;
}}
.stApp h1, .stApp h2, .stApp h3 {{ color: {INK}; font-weight: 600 !important; letter-spacing: -0.01em; }}
.block-container {{ max-width: 1120px; padding-top: 2.5rem; }}

.intro {{ max-width: 64ch; color: {INK}; font-size: 1.05rem; line-height: 1.55; margin-bottom: 1.5rem; }}
.intro a {{ color: {INK}; }}

/* The bill: the one distinctive element of the page */
.bill {{
  background: #F8FAFC;
  color: {INK};
  padding: 1.6rem 1.8rem 1.4rem;
  position: relative;
  box-shadow: 0 1px 0 {RULE};
  font-variant-numeric: tabular-nums;
}}
.bill::before {{
  /* perforated tear-off edge, like a paper phone bill */
  content: ""; position: absolute; left: 0; right: 0; top: -6px; height: 12px;
  background: radial-gradient(circle at 6px 6px, #E9EEF2 4px, transparent 4.5px) repeat-x;
  background-size: 14px 12px;
}}
.bill-head {{ display: flex; justify-content: space-between; align-items: baseline;
  border-bottom: 2px solid {INK}; padding-bottom: .6rem; margin-bottom: .4rem; }}
.bill-title {{ font-weight: 600; font-size: 1.15rem; }}
.bill-sub {{ color: #4A5A70; font-size: .9rem; }}
.bill-row {{ display: grid; grid-template-columns: 9.5rem 1fr 11rem 3.6rem; gap: .8rem;
  align-items: center; padding: .55rem 0; border-bottom: 1px dotted {RULE}; }}
.bill-row.cols {{ color: #4A5A70; font-size: .85rem; border-bottom: 1px solid {RULE}; padding: .3rem 0; }}
.bill-row .label {{ font-weight: 500; }}
.bill-row .num {{ text-align: right; }}
.ends {{ display: flex; justify-content: space-between; }}
.track {{ position: relative; height: 10px; background: linear-gradient(90deg, transparent 49.5%, {RULE} 49.5%, {RULE} 50.5%, transparent 50.5%); }}
.bar {{ position: absolute; top: 1px; height: 8px; }}
.bill-total {{ display: flex; justify-content: space-between; align-items: flex-end;
  border-top: 2px solid {INK}; margin-top: .9rem; padding-top: .9rem; }}
.total-label {{ font-weight: 600; font-size: 1.05rem; }}
.total-note {{ color: #4A5A70; font-size: .85rem; margin-top: .2rem; }}
.total-value {{ font-family: 'IBM Plex Sans Condensed', sans-serif; font-weight: 600;
  font-size: 3.6rem; line-height: .9; }}
.signal {{ display: flex; align-items: flex-end; gap: 4px; height: 30px; margin-top: .9rem; }}
.signal span {{ width: 9px; background: {RULE}; display: block; }}
.signal-text {{ margin-left: .7rem; font-size: .95rem; align-self: center; }}
.bill-foot {{ color: #4A5A70; font-size: .82rem; margin-top: 1rem; line-height: 1.45; max-width: 70ch; }}

.message {{ background: #F8FAFC; border-left: 4px solid {INK}; padding: 1rem 1.2rem;
  color: {INK}; line-height: 1.55; max-width: 70ch; }}
.big-fact {{ font-family: 'IBM Plex Sans Condensed', sans-serif; font-weight: 600;
  font-size: 2.6rem; color: {INK}; line-height: 1; }}
.fact-text {{ color: {INK}; max-width: 34ch; margin-top: .35rem; line-height: 1.45; }}

@media (max-width: 640px) {{
  .bill {{ padding: 1.2rem 1rem; }}
  .bill-row {{ grid-template-columns: 6.5rem 1fr 3.4rem; }}
  .bill-row .track-cell {{ display: none; }}
  .total-value {{ font-size: 2.8rem; }}
}}
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_data
def app_data():
    return load_app_data()


def risk_color(probability):
    return GREEN if probability < 0.25 else AMBER if probability < 0.5 else RED


def bill_html(profile, model):
    lines = risk_lines(profile, model)
    probability = churn_probability(profile, model)
    max_effect = max(abs(effect) for _, _, effect in lines) or 1

    rows = []
    for label, value, effect in lines:
        width = 50 * abs(effect) / max_effect
        left = 50 if effect >= 0 else 50 - width
        color = RED if effect > 0 else GREEN
        bar = f'<div class="bar" style="left:{left:.1f}%;width:{width:.1f}%;background:{color}"></div>' if effect else ""
        rows.append(
            f'<div class="bill-row"><div class="label">{label}</div>'
            f'<div class="track-cell"><div class="track">{bar}</div></div>'
            f'<div>{html.escape(value)}</div><div class="num">{effect:+.2f}</div></div>'
        )

    bars, strength = signal_bars(probability)
    color = risk_color(probability)
    signal = "".join(
        f'<span style="height:{8 + 7 * i}px;background:{color if i < bars else RULE}"></span>'
        for i in range(4)
    )
    average = app_data()["overall"]["churn_pct"]

    return f"""
<div class="bill">
  <div class="bill-head"><div class="bill-title">Churn risk statement</div>
    <div class="bill-sub">Simulated customer</div></div>
  <div class="bill-row cols"><div>Item</div><div class="track-cell ends"><span>Lowers</span><span>Raises</span></div>
    <div>Value</div><div class="num">Effect</div></div>
  {''.join(rows)}
  <div class="bill-total">
    <div><div class="total-label">Probability of leaving</div>
      <div class="total-note">Average across all customers: {average:.2f}%</div>
      <div class="signal">{signal}<div class="signal-text">Customer connection: {strength.lower()}</div></div>
    </div>
    <div class="total-value" style="color:{color}">{probability:.0%}</div>
  </div>
  <div class="bill-foot">Each effect is that item's contribution to the model's risk score
    (log-odds), starting from a base of {model['intercept']:+.2f}. Red items push the
    probability up and green items push it down. Associations, not proven causes.</div>
</div>"""


def setting(name):
    """Read a setting from Streamlit secrets (deployed) or .env (local)."""
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    try:
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    return os.getenv(name)


def live_message(profile, lang):
    key, base_url, model = setting("LLM_API_KEY"), setting("LLM_BASE_URL"), setting("LLM_MODEL")
    if not (key and base_url and model):
        return None
    from openai import OpenAI
    client = OpenAI(api_key=key, base_url=base_url, timeout=30)
    return generate_message(client, model, build_messages(profile, lang))


def bar_chart(rows, title, highlight):
    df = pd.DataFrame(rows)
    df["highlight"] = df["group"] == highlight
    return (
        alt.Chart(df, title=alt.Title(title, anchor="start", color=INK, fontWeight=600))
        .mark_bar(size=34)
        .encode(
            x=alt.X("group:N", sort=None, title=None, axis=alt.Axis(labelAngle=0, labelColor=INK)),
            y=alt.Y("churn_pct:Q", title="Churn rate (%)", axis=alt.Axis(grid=False, labelColor=INK, titleColor=INK)),
            color=alt.condition("datum.highlight", alt.value(RED), alt.value(INK)),
            tooltip=[alt.Tooltip("group:N", title="Group"), alt.Tooltip("customers:Q", title="Customers"),
                     alt.Tooltip("churn_pct:Q", title="Churn rate (%)")],
        )
        .properties(height=280)
        .configure_view(strokeWidth=0)
        .configure(background="transparent", font="IBM Plex Sans, Helvetica, Arial, sans-serif")
    )


data = app_data()
model = data["model"]

st.title("Which customers are about to leave?")
st.markdown(
    f'<p class="intro">A churn model trained on {data["overall"]["customers"]:,} customers '
    f'of the IBM Telco dataset. Build a customer below and read their risk like a phone bill. '
    f'Part of <a href="{REPO_URL}">telco-churn-end-to-end</a> by Luis Lazaro Machado.</p>',
    unsafe_allow_html=True,
)

tab_sim, tab_overview, tab_model = st.tabs(["Risk simulator", "What drives churn", "About the model"])

with tab_sim:
    left, right = st.columns([1, 1.9], gap="large")
    with left:
        st.subheader("Customer")
        tenure = st.slider("Months with the company", 0, 72, 3)
        contract = st.selectbox("Contract", ["Month-to-month", "One year", "Two year"])
        internet = st.selectbox("Internet service", ["Fiber optic", "DSL", "No"])
        payment = st.selectbox(
            "Payment method",
            ["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"],
        )
        charges = st.slider("Monthly charges", 18.0, 120.0, 107.95, step=0.05)
        with st.expander("Services (used only for the retention message)"):
            no_net = internet == "No"
            security = "No internet service" if no_net else st.radio("Online security", ["No", "Yes"], horizontal=True)
            support = "No internet service" if no_net else st.radio("Tech support", ["No", "Yes"], horizontal=True)

    profile = {
        "tenure": tenure,
        "Contract": contract,
        "InternetService": internet,
        "OnlineSecurity": security,
        "TechSupport": support,
        "PaymentMethod": payment,
        "MonthlyCharges": charges,
    }

    with right:
        st.markdown(bill_html(profile, model), unsafe_allow_html=True)

        st.subheader("Retention message")
        st.markdown(
            "An LLM (Google Gemini) writes a short message for this customer. It picks one "
            "offer from a fixed list and never mentions prices or the prediction."
        )
        used = st.session_state.get("messages_used", 0)
        lang_label = st.radio("Language", ["English", "Spanish"], horizontal=True)
        lang = "en" if lang_label == "English" else "es"
        clicked = st.button(
            "Write message", type="primary", disabled=used >= MESSAGES_PER_VISIT,
            help=f"Up to {MESSAGES_PER_VISIT} messages per visit, to protect the free API quota.",
        )
        if used >= MESSAGES_PER_VISIT:
            st.caption(f"You have used the {MESSAGES_PER_VISIT} messages for this visit.")
        if clicked:
            st.session_state["messages_used"] = used + 1
            with st.spinner("Writing the message..."):
                try:
                    text = live_message(profile, lang)
                except Exception:
                    text = None
            if text:
                st.markdown(f'<div class="message">{html.escape(text)}</div>', unsafe_allow_html=True)
                st.caption(f"Generated live. {MESSAGES_PER_VISIT - used - 1} left for this visit.")
            else:
                st.markdown(f'<div class="message">{html.escape(SAVED_EXAMPLE)}</div>', unsafe_allow_html=True)
                st.caption(
                    "Live generation is not available right now (the free API quota may be used up). "
                    "This is a saved example in English from a real run, for a new month-to-month fiber customer."
                )

with tab_overview:
    overall, high = data["overall"], data["high_risk"]
    c1, c2, c3 = st.columns(3)
    facts = [
        (f"{overall['churn_pct']:.2f}%", f"of customers left: {overall['churned']:,} of {overall['customers']:,}."),
        (f"{data['by_contract'][0]['churn_pct']:.2f}%",
         f"churn on month-to-month contracts, against {data['by_contract'][2]['churn_pct']:.2f}% on two-year contracts."),
        (f"{high['churn_pct']:.2f}%",
         f"churn among new, month-to-month, fiber optic customers ({high['churned']} of {high['customers']})."),
    ]
    for col, (value, text) in zip((c1, c2, c3), facts):
        col.markdown(f'<div class="big-fact">{value}</div><div class="fact-text">{text}</div>',
                     unsafe_allow_html=True)

    st.write("")
    g1, g2 = st.columns(2, gap="large")
    g1.altair_chart(bar_chart(data["by_contract"], "Churn by contract", "Month-to-month"), use_container_width=True)
    g2.altair_chart(bar_chart(data["by_tenure"], "Churn by months with the company", "0-11"), use_container_width=True)
    st.markdown(
        "**What to do:** offer incentives to move month-to-month customers to longer contracts, "
        "focusing on their first year."
    )

with tab_model:
    st.subheader("How the model compares")
    st.markdown(
        f"Logistic regression with 5 inputs, trained on {model['train_size']:,} customers and tested on "
        f"{model['test_size']:,} (every 5th row). AUC measures how well the model ranks customers who "
        "leave above those who stay: 0.5 is a coin flip, 1.0 is perfect."
    )
    auc = data["auc"]
    st.table(pd.DataFrame(
        [
            ["Logistic regression, Excel (Solver)", "0.815"],
            ["Logistic regression, Python", f"{auc['logistic_regression_python']:.3f}"],
            ["Random Forest, 5 inputs", f"{auc['random_forest_5_features']:.3f}"],
            ["Random Forest, 45 columns", "0.838"],
        ],
        columns=["Model", "AUC (test set)"],
    ).set_index("Model"))
    st.markdown(
        "The simulator uses the Python logistic regression: simple, explainable and within "
        "0.02 AUC of the best Random Forest. Limits: a single train/test split, five inputs, and "
        "associations rather than causes. The app stores only these coefficients and summary "
        "figures; no customer rows are published."
    )
    st.markdown(f"Code, notebook, SQL and Power BI files: [{REPO_URL}]({REPO_URL})")
