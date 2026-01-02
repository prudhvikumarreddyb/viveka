import streamlit as st
from datetime import datetime

from lifeos.utils.calculations import load_loans, save_loans


# =====================================================
# HELPERS
# =====================================================

def normalize_loan_no(val: str) -> str:
    return val.strip().lower()


def loan_no_exists(loans, loan_no, exclude_id=None):
    loan_no_norm = normalize_loan_no(loan_no)
    for l in loans:
        if exclude_id and l.get("id") == exclude_id:
            continue
        if normalize_loan_no(str(l.get("loan_no", l.get("id")))) == loan_no_norm:
            return True
    return False


def validate_emi_fields(loans, loan_no, lender, principal, total_months, emi, exclude_id=None):
    errors = []

    if not loan_no.strip():
        errors.append("Loan No is required")

    if loan_no_exists(loans, loan_no, exclude_id=exclude_id):
        errors.append("Loan No already exists")

    if not lender.strip():
        errors.append("Lender name is required")

    if principal <= 0:
        errors.append("Principal must be greater than 0")

    if total_months <= 0:
        errors.append("Total months must be greater than 0")

    if emi <= 0:
        errors.append("Monthly EMI must be greater than 0")

    return errors


def emi_progress(months_paid, total_months):
    if total_months <= 0:
        return 0.0
    return min(months_paid / total_months, 1.0)


# =====================================================
# MAIN PAGE
# =====================================================

def render_manage_loans():
    st.subheader("✏️ Manage EMI Loans")
    st.caption("EMI-only · Unique Loan No · Progress tracking")

    loans = load_loans()

    # Normalize data
    for l in loans:
        l.setdefault("archived", False)
        l.setdefault("months_paid", 0)
        l.setdefault("extra_paid", 0)
        l.setdefault("interest_only", False)
        l.setdefault("last_paid_month", "")

        if l.get("status") == "CLOSED":
            l["archived"] = True

    # Session state
    st.session_state.setdefault("edit_id", None)

    # =====================================================
    # ➕ ADD EMI LOAN
    # =====================================================
    st.markdown("## ➕ Add EMI Loan")

    loan_no = st.text_input("Loan No *", key="add_loan_no")
    lender = st.text_input("Lender *", key="add_lender")
    principal = st.number_input("Principal (₹)", min_value=0, key="add_principal")
    interest_rate = st.number_input(
        "Interest Rate (%)", min_value=0.0, step=0.1, key="add_rate"
    )
    total_months = st.number_input("Total Months", min_value=0, key="add_months")
    emi = st.number_input("Monthly EMI (₹)", min_value=0, key="add_emi")
    interest_only = st.checkbox("Interest-only loan", key="add_interest_only")

    if st.button("Add EMI Loan"):
        errors = validate_emi_fields(
            loans, loan_no, lender, principal, total_months, emi
        )

        if errors:
            for e in errors:
                st.error(e)
        else:
            loans.append({
                "id": loan_no.strip(),
                "loan_no": loan_no.strip(),
                "lender": lender.strip(),
                "type": "EMI",
                "status": "ACTIVE",
                "principal": principal,
                "interest_rate": interest_rate,
                "total_months": total_months,
                "months_paid": 0,
                "emi": emi,
                "extra_paid": 0,
                "interest_only": interest_only,
                "archived": False,
                "created_at": datetime.now().isoformat(),
            })

            save_loans(loans)
            st.success("EMI loan added")
            st.rerun()

    # =====================================================
    # 📋 ACTIVE EMI LOANS (WITH PROGRESS BAR)
    # =====================================================
    st.markdown("---")
    st.markdown("## 📋 Active EMI Loans")

    active_loans = [
        l for l in loans
        if l.get("type") == "EMI"
        and l.get("status") == "ACTIVE"
        and not l.get("archived")
    ]

    if not active_loans:
        st.info("No active EMI loans")
    else:
        for loan in active_loans:
            with st.container(border=True):
                c1, c2 = st.columns([7, 3])

                # Summary
                c1.markdown(
                    f"""
                    **{loan['lender']}**  
                    Loan No: `{loan.get('loan_no', loan.get('id'))}`  
                    EMI: ₹{loan['emi']:,}  
                    Principal: ₹{loan['principal']:,}  
                    Interest: {loan['interest_rate']}%  
                    """
                )

                # EMI Progress
                progress = emi_progress(
                    loan.get("months_paid", 0),
                    loan.get("total_months", 0)
                )

                c1.markdown(
                    f"**EMI Progress:** {loan['months_paid']} / {loan['total_months']} months"
                )
                c1.progress(progress)

                if loan.get("interest_only"):
                    c1.caption("Interest-only loan")

                # Actions
                if c2.button("✏️ Edit", key=f"edit_{loan['id']}"):
                    st.session_state.edit_id = loan["id"]

                if c2.button("🗄️ Archive", key=f"archive_{loan['id']}"):
                    loan["archived"] = True
                    loan["archived_at"] = datetime.now().isoformat()
                    save_loans(loans)
                    st.rerun()

    # =====================================================
    # ♻️ RESTORE ARCHIVED EMI LOANS
    # =====================================================
    st.markdown("---")
    show_archived = st.toggle("Show archived EMI loans")

    if show_archived:
        archived_loans = [
            l for l in loans
            if l.get("type") == "EMI"
            and l.get("archived")
            and l.get("status") == "ACTIVE"
        ]

        if not archived_loans:
            st.info("No archived EMI loans")
        else:
            for loan in archived_loans:
                with st.container(border=True):
                    c1, c2 = st.columns([7, 3])

                    c1.markdown(
                        f"""
                        **{loan['lender']}**  
                        Loan No: `{loan.get('loan_no', loan.get('id'))}`  
                        EMI ₹{loan['emi']:,}  
                        ⚪ ARCHIVED
                        """
                    )

                    if c2.button("♻️ Restore", key=f"restore_{loan['id']}"):
                        loan["archived"] = False
                        loan["restored_at"] = datetime.now().isoformat()
                        save_loans(loans)
                        st.rerun()

    # =====================================================
    # ✏️ EDIT EMI LOAN
    # =====================================================
    if st.session_state.edit_id:
        loan = next(l for l in loans if l["id"] == st.session_state.edit_id)

        st.markdown("---")
        st.markdown("## ✏️ Edit EMI Loan")

        loan_no = st.text_input(
            "Loan No *",
            value=loan.get("loan_no", loan.get("id")),
            key="edit_loan_no"
        )
        lender = st.text_input("Lender *", value=loan["lender"], key="edit_lender")
        principal = st.number_input(
            "Principal (₹)", min_value=0,
            value=int(loan["principal"]), key="edit_principal"
        )
        interest_rate = st.number_input(
            "Interest Rate (%)", min_value=0.0, step=0.1,
            value=float(loan["interest_rate"]), key="edit_rate"
        )
        total_months = st.number_input(
            "Total Months", min_value=0,
            value=int(loan["total_months"]), key="edit_months"
        )
        emi = st.number_input(
            "Monthly EMI (₹)", min_value=0,
            value=int(loan["emi"]), key="edit_emi"
        )
        interest_only = st.checkbox(
            "Interest-only loan",
            value=loan.get("interest_only", False),
            key="edit_interest_only"
        )

        c1, c2 = st.columns(2)

        if c1.button("💾 Save Changes"):
            errors = validate_emi_fields(
                loans, loan_no, lender, principal, total_months, emi,
                exclude_id=loan["id"]
            )

            if errors:
                for e in errors:
                    st.error(e)
            else:
                loan.update({
                    "id": loan_no.strip(),
                    "loan_no": loan_no.strip(),
                    "lender": lender.strip(),
                    "principal": principal,
                    "interest_rate": interest_rate,
                    "total_months": total_months,
                    "emi": emi,
                    "interest_only": interest_only,
                })

                save_loans(loans)
                st.session_state.edit_id = None
                st.success("EMI loan updated")
                st.rerun()

        if c2.button("Cancel"):
            st.session_state.edit_id = None
            st.rerun()
