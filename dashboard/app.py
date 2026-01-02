import streamlit as st
import sys
from pathlib import Path

# Add project root to Python path (Streamlit Cloud fix)
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from lifeos.utils.db import init_db

init_db()

from lifeos.pages.lifeos import render_lifeos
from lifeos.pages.cashflow import render_cashflow
from lifeos.utils.calculations import load_cashflow, load_loans
from lifeos.pages.manage_loans import render_manage_loans


# =====================================================
# 🚀 PAGE CONFIG (ONLY ONCE)
# =====================================================
st.set_page_config(page_title="Viveka", layout="wide")

# =====================================================
# 🧠 SESSION STATE (PAGE ROUTING)
# =====================================================
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# =====================================================
# 🎨 GLOBAL STYLES (SIDEBAR + THEME + TABLE READABILITY)
# =====================================================
st.markdown(
    """
    <style>
    /* -------------------------------
       Viveka title animation
    -------------------------------- */
    .viveka-title {
        font-size: 1.1rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        opacity: 0;
        transform: translateY(6px);
        animation: vivekaFadeUp 0.35s ease-out forwards;
        margin-bottom: 0.75rem;
    }

    @keyframes vivekaFadeUp {
        to { opacity: 1; transform: translateY(0); }
    }
    /* Improve vertical spacing between sections */
    section.main > div {
        padding-bottom: 0.75rem;
    }

    /* Add breathing room after headers */
    h2, h3 {
        margin-bottom: 0.75rem;
    }

    /* Reduce divider dominance */
    hr {
        margin-top: 1.25rem;
        margin-bottom: 1.25rem;
        opacity: 0.4;
    }

    /* -------------------------------
       Sidebar buttons
    -------------------------------- */
    section[data-testid="stSidebar"] button {
        width: 100%;
        text-align: left;
        border-radius: 6px;
        padding: 0.5rem 0.75rem;
        margin-bottom: 0.25rem;
        border-left: 4px solid transparent;
        transition:
            border-left-color 0.2s ease,
            padding-left 0.2s ease,
            font-weight 0.2s ease;
    }

    section[data-testid="stSidebar"] button.active-page {
        border-left-color: #2563EB;
        padding-left: 0.95rem;
        font-weight: 600;
    }

    /* -------------------------------
       Soft background
    -------------------------------- */
    body {
        background-color: #FAFAFA;
    }

    section[data-testid="stSidebar"] {
        background-color: #F3F4F6;
    }

    /* -------------------------------
       Section headers
    -------------------------------- */
    h2 {
        color: #1F2937;
        font-size: 1.25rem;
    }

    /* -------------------------------
       Alerts styling
    -------------------------------- */
    div[data-testid="stAlert"] {
        border-radius: 8px;
    }

    /* -------------------------------
       TABLE READABILITY
    -------------------------------- */
    div[data-testid="stDataFrame"] {
        font-size: 0.98rem;
    }

    div[data-testid="stDataFrame"] td,
    div[data-testid="stDataFrame"] th {
        padding-top: 0.55rem;
        padding-bottom: 0.55rem;
    }

    div[data-testid="stDataFrame"] th {
        font-weight: 600;
        color: #111827;
    }

    div[data-testid="stDataFrame"] td {
        font-variant-numeric: tabular-nums;
    }

    /* Metrics */
    div[data-testid="stMetricLabel"] {
        font-size: 0.9rem;
    }

    div[data-testid="stMetricValue"] {
        font-size: 1.6rem;
    }
    /* Progress captions readability */
    div[data-testid="stCaption"] {
        font-size: 0.9rem;
        color: #374151;  /* slate-700 */
    }
    /* Sidebar button text clarity */
    div[data-testid="stSidebar"] button {
        color: #111827; /* near-black */
    }

    /* Active sidebar highlight stronger */
    div[data-testid="stSidebar"] button.active-nav {
        background-color: #E5E7EB; /* light gray */
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# 🧭 SIDEBAR NAV BUTTON (FIXED, SINGLE SOURCE)
# =====================================================
def nav_button(label: str, page_key: str):
    is_active = st.session_state.page == page_key

    clicked = st.sidebar.button(
        label,
        key=f"nav_{page_key}",
        use_container_width=True
    )

    if clicked:
        st.session_state.page = page_key

    if is_active:
        st.markdown(
            f"""
            <script>
            const buttons = window.parent.document.querySelectorAll(
                'section[data-testid="stSidebar"] button'
            );
            buttons.forEach(btn => {{
                if (btn.innerText.trim() === "{label}") {{
                    btn.classList.add("active-page");
                }}
            }});
            </script>
            """,
            unsafe_allow_html=True
        )

# =====================================================
# 📊 DASHBOARD (FULL – UNCHANGED)
# =====================================================
def render_dashboard():
    st.title("Viveka Dashboard")
    st.caption("Overall financial health at a glance")

    # 💰 CASHFLOW SNAPSHOT
    cashflow = load_cashflow()
    income = cashflow.get("monthly_income", 0)
    fixed_expenses = sum(e.get("amount", 0) for e in cashflow.get("fixed_expenses", []))
    variable_expenses = sum(e.get("amount", 0) for e in cashflow.get("variable_expenses", []))
    total_expenses = fixed_expenses + variable_expenses
    surplus = income - total_expenses

    st.markdown("## Cashflow Snapshot")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Income", f"₹{income:,}")
    c2.metric("Expenses", f"₹{total_expenses:,}")
    c3.metric("Surplus", f"₹{surplus:,}")
    c4.metric("Status", "Healthy" if surplus >= 0 else "Deficit")

    # 📊 LIVING COST RATIO
    living_cost_ratio = (total_expenses / income) if income else 0
    living_cost_pct = round(living_cost_ratio * 100, 1)

    st.markdown("## Living Cost Ratio")
    r1, r2 = st.columns(2)
    r1.metric("Expenses / Income", f"{living_cost_pct}%")

    if living_cost_ratio <= 0.5:
        r2.success("Comfortable lifestyle cost")
    elif living_cost_ratio <= 0.7:
        r2.warning("Tight lifestyle cost")
    else:
        r2.error("High lifestyle cost risk")

    # 💳 EMI SNAPSHOT
    loans = load_loans()
    emi_loans = [l for l in loans if l["type"] == "EMI" and l["status"] == "ACTIVE"]
    total_emi = sum(l.get("emi", 0) for l in emi_loans)
    free_cash_after_emi = surplus - total_emi

    st.markdown("## EMI Snapshot")
    e1, e2, e3 = st.columns(3)
    e1.metric("Active EMIs", len(emi_loans))
    e2.metric("Monthly EMI", f"₹{total_emi:,}")
    e3.metric("Free Cash After EMI", f"₹{free_cash_after_emi:,}")

    # 📉 DEBT PRESSURE RATIO
    debt_pressure_ratio = (total_emi / income) if income else 0
    debt_pressure_pct = round(debt_pressure_ratio * 100, 1)

    st.markdown("## Debt Pressure Ratio")
    d1, d2 = st.columns(2)
    d1.metric("EMI / Income", f"{debt_pressure_pct}%")

    if debt_pressure_ratio <= 0.30:
        d2.success("Comfortable debt level")
    elif debt_pressure_ratio <= 0.45:
        d2.warning("Debt stretching income")
    else:
        d2.error("Dangerous debt pressure")

    # 💾 SAVINGS CAPACITY
    savings_capacity_ratio = (surplus / income) if income else 0
    savings_capacity_pct = round(savings_capacity_ratio * 100, 1)

    st.markdown("## Savings Capacity")
    s1, s2 = st.columns(2)
    s1.metric("Surplus / Income", f"{savings_capacity_pct}%")

    if savings_capacity_ratio >= 0.20:
        s2.success("Strong saving ability")
    elif savings_capacity_ratio >= 0.10:
        s2.warning("Weak saving ability")
    else:
        s2.error("No real savings capacity")

    # 🚨 OVERALL SIGNAL
    if free_cash_after_emi < 0:
        st.error(
            "Critical financial stress.\n\n"
            "Income cannot support expenses and EMIs.\n"
            "Immediate priority: reduce expenses or close one EMI."
        )
    elif free_cash_after_emi < 10000:
        st.warning(
            "Very tight cashflow.\n\n"
            "Avoid new expenses and focus on EMI reduction."
        )
    else:
        st.success(
            "Financial position is stable.\n\n"
            "You can save or close EMIs faster."
        )

# =====================================================
# 📌 SIDEBAR
# =====================================================
st.sidebar.markdown(
    """
    <div class="viveka-title">🧠 VIVEKA</div>
    <div class="viveka-caption">Personal Financial Clarity System</div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Overview")
nav_button("📊 Dashboard", "dashboard")

st.sidebar.markdown("---")
st.sidebar.markdown("### LifeOS")
nav_button("💳 Loans", "loans")
nav_button("✏️ Manage Loans", "manage_loans")
nav_button("💰 Cashflow", "cashflow")

# =====================================================
# 🧭 PAGE ROUTING
# =====================================================
if st.session_state.page == "dashboard":
    render_dashboard()
elif st.session_state.page == "loans":
    render_lifeos()
elif st.session_state.page == "manage_loans":
    render_manage_loans()

elif st.session_state.page == "cashflow":
    render_cashflow()
st.caption("Viveka • Personal Financial Clarity System")
