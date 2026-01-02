# 🧠 Viveka — Personal Financial Operating System

Viveka is a **personal financial clarity and execution system** built using **Python + Streamlit**.

Its goal is not just to track money, but to:
- Understand cashflow
- Control EMIs and debt
- Track settlements
- Measure financial pressure
- Drive **monthly execution**, not just analysis

This app is designed **only for personal use** and prioritizes clarity over complexity.

---

## 🚀 Tech Stack

- **Python 3.10+**
- **Streamlit** (UI & state management)
- **JSON** (data persistence)
- **Pandas** (tables & calculations)

---

## 📂 Project Structure

```text
viveka/
├── dashboard/
│ └── app.py # Main app entry & navigation
├── lifeos/
│ ├── pages/
│ │ ├── lifeos.py # Loans, EMI risk, settlements
│ │ └── cashflow.py # Income & expense management
│ ├── utils/
│ │ └── calculations.py # Data loading & saving
│ └── data/
│ ├── loans.json
│ └── cashflow.json
├── .streamlit/
│ └── config.toml # Light theme, soft colors
├── README.md
├── .editorconfig
└── .pre-commit-config.yaml


---

## 🧭 App Pages & Responsibilities

### 📊 Dashboard
- Financial health overview
- EMI pressure
- Living cost ratio
- Savings capacity

### 💳 LifeOS (Loans)
- EMI tracking (principal, interest, balance)
- EMI risk score (income-aware)
- Prepayment simulator
- Settlement tracking (31% benchmark)
- Closed loan analysis

### 💰 Cashflow
- Monthly income
- Fixed & variable expenses
- Monthly surplus

---

## 🧠 Key Metrics Explained

- **EMI Risk Score (0–100)**  
  Measures affordability using:
  - EMI / Income
  - Free cash after EMI
  - Interest-only loans
  - Number of EMIs
  - Remaining tenure

- **31% Benchmark**  
  Settlement comparison baseline based on real-world outcomes.

---

## 🚀 How to Run

```bash
streamlit run dashboard/app.py
