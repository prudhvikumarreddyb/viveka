import streamlit as st
import json
from pathlib import Path

DATA_FILE = Path(__file__).parents[1] / "data" / "cashflow.json"


# =====================================================
# 📦 DATA HELPERS
# =====================================================

from lifeos.utils.db import get_connection

def load_cashflow():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT monthly_income FROM cashflow WHERE id=1")
    row = cur.fetchone()
    income = row[0] if row else 0

    cur.execute("SELECT name, amount FROM expenses WHERE type='fixed'")
    fixed = [{"name": r[0], "amount": r[1]} for r in cur.fetchall()]

    cur.execute("SELECT name, amount FROM expenses WHERE type='variable'")
    variable = [{"name": r[0], "amount": r[1]} for r in cur.fetchall()]

    conn.close()

    return {
        "monthly_income": income,
        "fixed_expenses": fixed,
        "variable_expenses": variable
    }
def save_cashflow(data):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM cashflow")
    cur.execute("INSERT INTO cashflow (id, monthly_income) VALUES (1, ?)",
                (data["monthly_income"],))

    cur.execute("DELETE FROM expenses")

    for e in data["fixed_expenses"]:
        cur.execute(
            "INSERT INTO expenses (type, name, amount) VALUES (?, ?, ?)",
            ("fixed", e["name"], e["amount"])
        )

    for e in data["variable_expenses"]:
        cur.execute(
            "INSERT INTO expenses (type, name, amount) VALUES (?, ?, ?)",
            ("variable", e["name"], e["amount"])
        )

    conn.commit()
    conn.close()

# =====================================================
# 💰 CASHFLOW PAGE
# =====================================================

def render_cashflow():
    st.subheader("💰 Cashflow – Income & Expenses")

    data = load_cashflow()

    # ================================
    # 💼 INCOME
    # ================================

    st.markdown("## 💼 Monthly Income")

    income = st.number_input(
        "Total Monthly Income (₹)",
        min_value=0,
        step=1000,
        value=int(data.get("monthly_income", 0))
    )

    # ================================
    # 🧾 FIXED EXPENSES
    # ================================

    st.markdown("## 🧾 Fixed Expenses")

    fixed_rows = []
    for item in data.get("fixed_expenses", []):
        fixed_rows.append(item)

    fixed_df = st.data_editor(
        fixed_rows,
        num_rows="dynamic",
        key="fixed_expenses",
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Expense"),
            "amount": st.column_config.NumberColumn("Amount (₹)", min_value=0)
        }
    )

    fixed_total = sum(row.get("amount", 0) for row in fixed_df)

    # ================================
    # 🛒 VARIABLE EXPENSES
    # ================================

    st.markdown("## 🛒 Variable Expenses")

    variable_rows = []
    for item in data.get("variable_expenses", []):
        variable_rows.append(item)

    variable_df = st.data_editor(
        variable_rows,
        num_rows="dynamic",
        key="variable_expenses",
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Expense"),
            "amount": st.column_config.NumberColumn("Amount (₹)", min_value=0)
        }
    )

    variable_total = sum(row.get("amount", 0) for row in variable_df)

    # ================================
    # 📊 SUMMARY
    # ================================

    st.markdown("## 📊 Monthly Summary")

    total_expenses = fixed_total + variable_total
    surplus = income - total_expenses
    expense_ratio = (total_expenses / income) if income else 0
    expense_pct = round(expense_ratio * 100, 1)

    savings_ratio = (surplus / income) if income else 0
    savings_pct = round(savings_ratio * 100, 1)

    c1, c2, c3, c4, c5, c6 = st.columns(6)

    c1.metric("Income", f"₹{income:,}")
    c2.metric("Fixed Expenses", f"₹{fixed_total:,}")
    c3.metric("Variable Expenses", f"₹{variable_total:,}")
    c4.metric("Expense Ratio", f"{expense_pct}%")
    c5.metric("Savings Ratio", f"{savings_pct}%")
    if surplus >= 0:
        c6.metric("Surplus", f"₹{surplus:,}", delta="Healthy ✅")
    else:
        c6.metric("Deficit", f"₹{surplus:,}", delta="Risk ⚠️")


    # ================================
    # 💾 SAVE
    # ================================

    if st.button("💾 Save Cashflow"):
        data["monthly_income"] = income
        data["fixed_expenses"] = fixed_df
        data["variable_expenses"] = variable_df
        save_cashflow(data)
        st.success("Cashflow saved successfully ✅")
    st.caption(
    "ℹ️ Your expense and savings ratios directly influence Dashboard signals "
    "like lifestyle cost, savings capacity, and debt pressure."
    )
