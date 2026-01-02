import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parents[1] / "data" / "viveka.db"

def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Cashflow
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cashflow (
        id INTEGER PRIMARY KEY,
        monthly_income INTEGER
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT,
        name TEXT,
        amount INTEGER
    )
    """)

    # Loans
    cur.execute("""
    CREATE TABLE IF NOT EXISTS loans (
        id INTEGER PRIMARY KEY,
        lender TEXT,
        type TEXT,
        status TEXT,
        principal INTEGER,
        emi INTEGER,
        total_months INTEGER,
        months_paid INTEGER,
        interest_rate REAL,
        extra_paid INTEGER,
        latest_offer INTEGER,
        last_paid_month TEXT
    )
    """)

    conn.commit()
    conn.close()
