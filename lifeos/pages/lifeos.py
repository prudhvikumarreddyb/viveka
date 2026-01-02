import streamlit as st
import pandas as pd
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from lifeos.utils.calculations import load_loans, save_loans, load_cashflow


# =====================================================
# 🔁 HELPERS
# =====================================================

def calculate_new_emi(principal, annual_rate, months):
    if principal <= 0 or months <= 0:
        return 0
    r = annual_rate / 12 / 100
    emi = principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
    return round(emi)


def current_month_key():
    return datetime.now().strftime("%Y-%m")


def diff_31_style(val):
    try:
        val = float(val)
        if val < 0:
            return "background-color:#DCFCE7; color:#166534;"
        elif val > 0:
            return "background-color:#FEE2E2; color:#991B1B;"
        return ""
    except Exception:
        return ""


# =====================================================
# 📊 EMI PROGRESS HELPERS
# =====================================================

def emi_progress(months_paid, total_months):
    if total_months <= 0:
        return 0.0
    return min(months_paid / total_months, 1.0)


def progress_color(progress):
    if progress >= 0.7:
        return "🟢"
    elif progress >= 0.4:
        return "🟡"
    return "🔴"


def remaining_balance_estimate(loan):
    emi = loan.get("emi", 0)
    total_months = loan.get("total_months", 0)
    months_paid = loan.get("months_paid", 0)
    extra_paid = loan.get("extra_paid", 0)

    total_payable = emi * total_months
    paid = (emi * months_paid) + extra_paid

    return max(total_payable - paid, 0)


def projected_close_date(months_left):
    if months_left <= 0:
        return "Completed"
    close_date = date.today() + relativedelta(months=months_left)
    return close_date.strftime("%b %Y")


# =====================================================
# 🚨 EMI RISK SCORE
# =====================================================

def render_risk_badge(score: int):
    if score <= 25:
        st.success(f"🟢 Risk Score: {score}/100 — Safe")
    elif score <= 50:
        st.warning(f"🟡 Risk Score: {score}/100 — Watch")
    elif score <= 75:
        st.warning(f"🟠 Risk Score: {score}/100 — Stress")
    else:
        st.error(f"🔴 Risk Score: {score}/100 — Danger")


def calculate_emi_risk_score(emi_loans, income, expenses):
    if not emi_loans or income <= 0:
        return 0

    total_emi = sum(l.get("emi", 0) for l in emi_loans)
    surplus = income - expenses
    free_cash = surplus - total_emi

    score = 0

    emi_ratio = total_emi / income
    if emi_ratio > 0.45:
        score += 40
    elif emi_ratio > 0.30:
        score += 25
    elif emi_ratio > 0.20:
        score += 10

    if free_cash < 0:
        score += 25
    elif free_cash < 10_000:
        score += 15
    elif free_cash < 25_000:
        score += 5

    if any(l.get("interest_only") for l in emi_loans):
        score += 15

    if len(emi_loans) >= 5:
        score += 10
    elif len(emi_loans) >= 3:
        score += 5

    for l in emi_loans:
        if (l["total_months"] - l["months_paid"]) > 36:
            score += 10
            break

    return min(score, 100)


# =====================================================
# 🧠 LIFEOS MAIN
# =====================================================

def render_lifeos(loans=None):
    st.subheader("🧠 LifeOS – Financial Clarity System")

    if loans is None:
        loans = load_loans()

    cashflow = load_cashflow()

    for l in loans:
        l.setdefault("extra_paid", 0)
        l.setdefault("latest_offer", 0)
        l.setdefault("last_paid_month", "")

    emi_loans = [l for l in loans if l["type"] == "EMI" and l["status"] == "ACTIVE"]
    settlement_loans = [l for l in loans if l["type"] == "SETTLEMENT" and l["status"] == "ACTIVE"]
    closed_loans = [l for l in loans if l["status"] == "CLOSED"]

    # =====================================================
    # 🔢 SORT EMI LOANS (closest to completion first)
    # =====================================================

    emi_loans = sorted(
        emi_loans,
        key=lambda l: (l["total_months"] - l["months_paid"])
    )

    # =====================================================
    # 💳 EMI SNAPSHOT
    # =====================================================

    income = cashflow.get("monthly_income", 0)
    fixed = sum(e.get("amount", 0) for e in cashflow.get("fixed_expenses", []))
    variable = sum(e.get("amount", 0) for e in cashflow.get("variable_expenses", []))
    expenses = fixed + variable

    total_emi = sum(l.get("emi", 0) for l in emi_loans)

    st.markdown("## 💳 EMI Snapshot")
    c1, c2 = st.columns(2)
    c1.metric("Active EMIs", len(emi_loans))
    c2.metric("Monthly EMI", f"₹{total_emi:,}")

    risk = calculate_emi_risk_score(emi_loans, income, expenses)
    render_risk_badge(risk)

    # =====================================================
    # 🧠 AI INSIGHT
    # =====================================================

    if emi_loans:
        next_close = emi_loans[0]
        months_left = next_close["total_months"] - next_close["months_paid"]

        st.info(
            f"💡 **Insight:** Closing **{next_close['lender']}** next "
            f"({months_left} EMIs left) can free **₹{next_close['emi']:,}/month** "
            f"and improve cashflow."
        )

    # =====================================================
    # 📈 EMI PROGRESS OVERVIEW (ENHANCED)
    # =====================================================

    if emi_loans:
        st.markdown("## 📈 EMI Progress Overview")

        for l in emi_loans:
            months_left = l["total_months"] - l["months_paid"]
            progress = emi_progress(l["months_paid"], l["total_months"])
            percent = int(progress * 100)
            balance = remaining_balance_estimate(l)
            badge = progress_color(progress)
            close_by = projected_close_date(months_left)

            st.markdown(f"**{l['lender']}**  \nLoan No: `{l['id']}`")
            st.progress(progress)
            st.caption(
                f"{badge} **{percent}% complete** · "
                f"**{months_left} EMIs left** · "
                f"Close by **{close_by}**"
            )
            #st.markdown(f"Remaining balance (est.): **₹{balance:,}**")
            st.markdown("---")

    # =====================================================
    # 📊 EMI LOANS SUMMARY
    # =====================================================

    total_principal = total_interest = total_payable = 0
    total_paid = total_balance = total_pending = 0

    for l in emi_loans:
        principal = l["principal"]
        emi = l["emi"]
        total_m = l["total_months"]
        paid_m = l["months_paid"]
        extra = l["extra_paid"]
        interest_only = l.get("interest_only", False)

        if interest_only:
            interest = emi * total_m
            payable = principal + interest
            paid = emi * paid_m + extra
            balance = principal
        else:
            payable = emi * total_m
            interest = payable - principal
            paid = emi * paid_m + extra
            balance = max(payable - paid, 0)

        total_principal += principal
        total_interest += interest
        total_payable += payable
        total_paid += paid
        total_balance += balance
        total_pending += (total_m - paid_m)

    st.markdown("### 📊 EMI Loans Summary")
    s1, s2, s3, s4, s5, s6 = st.columns(6)
    s1.metric("Principal", f"₹{total_principal:,}")
    s2.metric("Interest", f"₹{total_interest:,}")
    s3.metric("Total Payable", f"₹{total_payable:,}")
    s4.metric("Paid", f"₹{total_paid:,}")
    s5.metric("Balance", f"₹{total_balance:,}")
    s6.metric("Pending EMIs", total_pending)

    # =====================================================
    # 💳 EMI LOANS TABLE
    # =====================================================

    st.markdown("## 💳 EMI Loans")
    edit_emi = st.toggle("Edit EMI Extra Payments", value=False)

    rows = []
    for l in emi_loans:
        principal = l["principal"]
        emi = l["emi"]
        total_m = l["total_months"]
        paid_m = l["months_paid"]
        extra = l["extra_paid"]
        rate = float(l.get("interest_rate", 0))
        interest_only = l.get("interest_only", False)

        if interest_only:
            interest = emi * total_m
            payable = principal + interest
            paid = emi * paid_m + extra
            balance = principal
        else:
            payable = emi * total_m
            interest = payable - principal
            paid = emi * paid_m + extra
            balance = max(payable - paid, 0)

        rows.append({
            "Loan No": l["id"],
            "Lender": l["lender"],
            "Interest Rate (%)": round(rate, 2),
            "Principal (₹)": principal,
            "Interest (₹)": interest,
            "Total Payable (₹)": payable,
            "EMI (₹)": emi,
            "Paid EMIs": f"{paid_m}/{total_m}",
            "Pending EMIs": total_m - paid_m,
            "Extra Paid (₹)": extra,
            "Paid (₹)": paid,
            "Balance (₹)": balance,
        })

    df_emi = pd.DataFrame(rows)

    if edit_emi:
        st.caption("Edit Extra Paid amounts in the table. TOTAL row is not displayed while editing.")
        edited = st.data_editor(
            df_emi,
            hide_index=True,
            use_container_width=True,
            disabled=[
                "Loan No", "Lender", "Interest Rate (%)",
                "Principal (₹)", "Interest (₹)", "Total Payable (₹)",
                "EMI (₹)", "Paid EMIs", "Pending EMIs",
                "Paid (₹)", "Balance (₹)"
            ],
        )

        if not edited.equals(df_emi):
            # filter out blank Loan No rows (safety) and create updates
            clean = edited[edited["Loan No"].astype(str).str.strip() != ""]
            for _, row in clean.iterrows():
                loan_id = row["Loan No"]
                for loan in loans:
                    if loan["id"] == loan_id:
                        # protect against non-int / NaN
                        try:
                            loan["extra_paid"] = int(row.get("Extra Paid (₹)") or 0)
                        except Exception:
                            loan["extra_paid"] = 0
                        break
            save_loans(loans)
            st.rerun()
    else:
        st.dataframe(
            df_emi.style.format({"Interest Rate (%)": "{:.2f}"}),
            use_container_width=True,
        )

    # =====================================================
    # ✅ MARK / UNDO EMI PAID (ONCE PER MONTH)
    # =====================================================

    st.markdown("## ✅ Mark EMI Paid (This Month)")
    current_month = current_month_key()

    for l in emi_loans:
        col1, col2, col3 = st.columns([4, 2, 2])

        col1.markdown(f"**{l['lender']}**  \nLoan No: `{l['id']}`")
        col2.markdown(f"EMIs Paid: **{l['months_paid']}/{l['total_months']}**")

        # Completed loan
        if l["months_paid"] >= l["total_months"]:
            col3.button(
                "Completed",
                disabled=True,
                key=f"done_{l['id']}_completed",
                use_container_width=True,
            )
            continue

        # If already paid this month -> show Undo
        if l.get("last_paid_month") == current_month:
            if col3.button(
                "Undo EMI Paid",
                key=f"undo_{l['id']}_{current_month}",
                use_container_width=True,
            ):
                for loan in loans:
                    if loan["id"] == l["id"] and loan["months_paid"] > 0:
                        loan["months_paid"] -= 1
                        loan["last_paid_month"] = ""
                        break
                save_loans(loans)
                st.warning(f"EMI payment undone for {l['lender']}")
                st.rerun()
        else:
            # Mark paid for current month
            if col3.button(
                "Mark EMI Paid",
                key=f"pay_{l['id']}_{current_month}",
                use_container_width=True,
            ):
                for loan in loans:
                    if loan["id"] == l["id"]:
                        loan["months_paid"] += 1
                        loan["last_paid_month"] = current_month
                        break
                save_loans(loans)
                st.success(f"EMI marked paid for {l['lender']}")
                st.rerun()

    # =====================================================
    # 🧩 SETTLEMENT SUMMARY
    # =====================================================

    if settlement_loans:
        st.markdown("### 📊 Settlement Summary")
        s1, s2, s3 = st.columns(3)
        s1.metric("Outstanding", f"₹{sum(l['outstanding'] for l in settlement_loans):,}")
        s2.metric("31% Target", f"₹{sum(int(l['outstanding'] * 0.31) for l in settlement_loans):,}")
        s3.metric("Latest Offers", f"₹{sum(l['latest_offer'] for l in settlement_loans):,}")

    # =====================================================
    # 🧩 SETTLEMENT LOANS TABLE (EDITABLE)
    # =====================================================

    st.markdown("## 🧩 Settlement Loans")
    edit_settle = st.toggle("Edit Settlement Offers", value=False)

    rows = []
    for l in settlement_loans:
        target_31 = int(l["outstanding"] * 0.31)
        rows.append({
            "Loan No": l["id"],
            "Lender": l["lender"],
            "Outstanding (₹)": l["outstanding"],
            "31% Target (₹)": target_31,
            "Latest Offer (₹)": l.get("latest_offer", 0),
            "Diff vs 31% (₹)": int(l.get("latest_offer", 0)) - target_31,
            "Mark Settled": False,
            "Settled Date": date.today(),
        })

    df_settle = pd.DataFrame(rows)

    if edit_settle:
        st.caption("Edit Latest Offer and mark settled if you've closed the account.")
        edited = st.data_editor(
            df_settle,
            hide_index=True,
            use_container_width=True,
            disabled=[
                "Loan No", "Lender", "Outstanding (₹)", "31% Target (₹)", "Diff vs 31% (₹)"
            ],
        )

        if not edited.equals(df_settle):
            clean = edited[edited["Loan No"].astype(str).str.strip() != ""]
            updates = clean.set_index("Loan No").to_dict("index")
            for loan in loans:
                if loan["id"] in updates:
                    row = updates[loan["id"]]
                    try:
                        loan["latest_offer"] = int(row.get("Latest Offer (₹)") or 0)
                    except Exception:
                        loan["latest_offer"] = 0
                    if row.get("Mark Settled"):
                        loan["status"] = "CLOSED"
                        loan["settlement_amount"] = loan["latest_offer"]
                        loan["settled_date"] = str(row.get("Settled Date") or date.today())
            save_loans(loans)
            st.rerun()
    else:
        if not df_settle.empty:
            st.dataframe(
                df_settle
                .style
                .applymap(diff_31_style, subset=["Diff vs 31% (₹)"]),
                use_container_width=True,
            )
        else:
            st.info("No active settlement loans")

    # =====================================================
    # 📊 CLOSED LOANS SUMMARY
    # =====================================================

    if closed_loans:
        st.markdown("### 📊 Closed Loans Summary")
        c1, c2, c3, c4 = st.columns(4)
        total_out = sum(l["outstanding"] for l in closed_loans)
        total_paid = sum(l["settlement_amount"] for l in closed_loans)
        total_31 = sum(int(l["outstanding"] * 0.31) for l in closed_loans)
        c1.metric("Outstanding", f"₹{total_out:,}")
        c2.metric("31% Benchmark", f"₹{total_31:,}")
        c3.metric("Paid", f"₹{total_paid:,}")
        c4.metric("Saved", f"₹{total_out - total_paid:,}")

    # =====================================================
    # ✅ CLOSED LOANS TABLE
    # =====================================================

    st.markdown("## ✅ Closed Loans")

    rows = []
    for l in closed_loans:
        target_31 = int(l["outstanding"] * 0.31)
        rows.append({
            "Loan No": l["id"],
            "Lender": l["lender"],
            "Outstanding (₹)": l["outstanding"],
            "31% Benchmark (₹)": target_31,
            "Paid (₹)": l["settlement_amount"],
            "Above / Below 31% (₹)": l["settlement_amount"] - target_31,
        })

    if rows:
        df_closed = pd.DataFrame(rows)
        st.dataframe(
            df_closed.style.applymap(diff_31_style, subset=["Above / Below 31% (₹)"]),
            use_container_width=True,
        )
    else:
        st.info("No closed loans yet")
