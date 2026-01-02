import json
from pathlib import Path

# -------------------------------------------------
# DATA FILE PATH
# -------------------------------------------------
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "loans.json"


# -------------------------------------------------
# LOAD / SAVE
# -------------------------------------------------
def load_loans():
    """Load all loans from JSON file"""
    with open(DATA_PATH, "r") as f:
        return json.load(f)


def save_loans(loans):
    """Persist loans back to JSON file"""
    with open(DATA_PATH, "w") as f:
        json.dump(loans, f, indent=2)


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
