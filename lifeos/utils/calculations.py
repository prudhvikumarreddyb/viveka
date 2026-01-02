import json
from pathlib import Path

# -------------------------------------------------
# DATA FILE PATH
# -------------------------------------------------
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "loans.json"


# -------------------------------------------------
# LOAD / SAVE
# -------------------------------------------------
from lifeos.utils.db import get_connection

def load_loans():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM loans")
    cols = [c[0] for c in cur.description]
    loans = [dict(zip(cols, row)) for row in cur.fetchall()]

    conn.close()
    return loans

def save_loans(loans):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM loans")

    for l in loans:
        cur.execute("""
        INSERT INTO loans (
            id, lender, type, status, principal, emi,
            total_months, months_paid, interest_rate,
            extra_paid, latest_offer, last_paid_month
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            l["id"], l["lender"], l["type"], l["status"],
            l["principal"], l["emi"],
            l["total_months"], l["months_paid"],
            l.get("interest_rate", 0),
            l.get("extra_paid", 0),
            l.get("latest_offer", 0),
            l.get("last_paid_month", "")
        ))

    conn.commit()
    conn.close()

# -------------------------------------------------
# FILTERS
# -------------------------------------------------
def active_emis(loans):
    return [
        l for l in loans
        if l.get("type") == "EMI" and l.get("status") == "ACTIVE"
    ]


def active_settlements(loans):
    return [
        l for l in loans
        if l.get("type") == "SETTLEMENT" and l.get("status") == "ACTIVE"
    ]


def closed_settlements(loans):
    return [
        l for l in loans
        if l.get("type") == "SETTLEMENT" and l.get("status") == "CLOSED"
    ]


# -------------------------------------------------
# METRICS
# -------------------------------------------------
def total_monthly_emi(loans):
    return sum(l["emi"] for l in active_emis(loans))


def emi_progress(loan):
    if not loan.get("total_months"):
        return 0
    return round((loan["months_paid"] / loan["total_months"]) * 100, 1)


def load_cashflow():
    data_file = Path(__file__).parents[1] / "data" / "cashflow.json"
    if not data_file.exists():
        return {
            "monthly_income": 0,
            "fixed_expenses": [],
            "variable_expenses": []
        }
    with open(data_file, "r") as f:
        return json.load(f)
