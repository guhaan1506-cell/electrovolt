"""
Personal Finance Chatbot (console)
Features:
 - User profile (saved locally in JSON)
 - Savings projection
 - Emergency fund recommendation
 - Investment projection (monthly SIP / lump sum)
 - Configurable tax estimator (you input slabs / rates)
 - Simple retirement projection
 - Friendly, step-by-step CLI interaction
"""

import json
import math
import os
from datetime import datetime

DATA_FILE = "pf_chatbot_user.json"

# ---------------- Utility functions ----------------
def format_currency(x):
    try:
        x = float(x)
    except:
        return str(x)
    # Basic formatting (no locale dependency)
    return f"₹{x:,.2f}"

def save_user(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def load_user():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def get_float(prompt, default=None):
    while True:
        try:
            s = input(prompt).strip()
            if s == "" and default is not None:
                return default
            val = float(s.replace(",", ""))
            return val
        except ValueError:
            print("  Please enter a valid number (e.g. 15000 or 15000.50).")

def get_int(prompt, default=None):
    while True:
        try:
            s = input(prompt).strip()
            if s == "" and default is not None:
                return default
            val = int(s)
            return val
        except ValueError:
            print("  Please enter a valid integer.")

# ---------------- Financial calculators ----------------

def savings_projection(monthly_saving, annual_rate_pct, years):
    """Future value of a monthly saving into an account with compounding monthly."""
    r = annual_rate_pct / 100.0 / 12.0
    n = years * 12
    fv = 0.0
    for _ in range(n):
        fv = (fv + monthly_saving) * (1 + r)
    return fv

def lump_sum_growth(principal, annual_rate_pct, years):
    """Future value of a one-time investment with annual compounding."""
    r = annual_rate_pct / 100.0
    return principal * ((1 + r) ** years)

def sip_needed(goal_amount, annual_rate_pct, years):
    """Monthly SIP needed to reach goal_amount given expected annual return."""
    r = annual_rate_pct / 100.0 / 12.0
    n = years * 12
    if r == 0:
        return goal_amount / n
    # formula for annuity: payment = FV * r / ((1+r)^n - 1)
    payment = goal_amount * r / ((1 + r) ** n - 1)
    return payment

def emergency_fund_recommendation(monthly_expenses, months=6):
    return monthly_expenses * months

def retirement_projection(current_savings, monthly_contrib, years_to_retire, annual_return_pct):
    """Estimate corpus at retirement from current savings + monthly contrib."""
    lump = lump_sum_growth(current_savings, annual_return_pct, years_to_retire)
    sip_future = savings_projection(monthly_contrib, annual_return_pct, years_to_retire)
    return lump + sip_future

# ---------------- Tax estimator (configurable) ----------------
def estimate_tax(taxable_income, slabs):
    """
    slabs: list of tuples (upper_limit, rate_pct) in ascending order.
    last slab can have upper_limit = None meaning 'rest'.
    Example: [(250000, 0), (500000, 5), (1000000, 20), (None, 30)]
    """
    tax = 0.0
    prev_limit = 0.0
    remaining = taxable_income
    for limit, rate in slabs:
        if limit is None:
            taxable_here = remaining
        else:
            taxable_here = max(0.0, min(remaining, limit - prev_limit))
        if taxable_here <= 0:
            prev_limit = limit if limit is not None else prev_limit
            continue
        tax += taxable_here * (rate / 100.0)
        remaining -= taxable_here
        prev_limit = limit if limit is not None else prev_limit
        if remaining <= 0:
            break
    return tax

# ---------------- CLI actions ----------------

def setup_profile(user):
    print("\n--- Setup Profile ---")
    name = input("Your name: ").strip() or user.get("name", "")
    monthly_income = get_float("Monthly take-home income (₹): ", user.get("monthly_income", 0.0))
    monthly_expenses = get_float("Average monthly expenses (₹): ", user.get("monthly_expenses", 0.0))
    savings_rate_guess = 0.0
    if monthly_income > 0:
        savings_rate_guess = max(0.0, (monthly_income - monthly_expenses) / monthly_income * 100.0)
    print(f"Estimated savings rate: {savings_rate_guess:.1f}% (based on income & expenses)")
    user.update({
        "name": name,
        "monthly_income": monthly_income,
        "monthly_expenses": monthly_expenses,
        "updated": datetime.utcnow().isoformat()
    })
    save_user(user)
    print("Profile saved.\n")
    return user

def run_savings_projection(user):
    print("\n--- Savings Projection ---")
    monthly = get_float("How much can you save monthly? (₹): ", user.get("monthly_income", 0.0) - user.get("monthly_expenses", 0.0))
    rate = get_float("Expected annual return rate (%) (e.g., 6 for bank FD, 12 for balanced funds): ", 8.0)
    years = get_int("For how many years will you save? (years): ", 10)
    fv = savings_projection(monthly, rate, years)
    print(f"In {years} years, saving {format_currency(monthly)} monthly at {rate}% pa => {format_currency(fv)}\n")

def run_emergency_recommendation(user):
    print("\n--- Emergency Fund ---")
    monthly_expenses = get_float("What are your monthly essential expenses (₹): ", user.get("monthly_expenses", 0.0))
    months = get_int("How many months of cover do you want? (typical 3-12): ", 6)
    eh = emergency_fund_recommendation(monthly_expenses, months)
    print(f"Recommended emergency fund: {months} × {format_currency(monthly_expenses)} = {format_currency(eh)}\n")

def run_investment_projection(user):
    print("\n--- Investment Projection (SIP & Lump Sum) ---")
    choice = input("1) Monthly SIP projection  2) Lump-sum growth  (enter 1 or 2): ").strip()
    if choice == "1":
        monthly = get_float("Monthly SIP amount (₹): ", 5000.0)
        rate = get_float("Expected annual return (%) : ", 12.0)
        years = get_int("Investment period (years): ", 10)
        fv = savings_projection(monthly, rate, years)
        print(f"Monthly {format_currency(monthly)} for {years} years at {rate}% pa -> {format_currency(fv)}")
    else:
        principal = get_float("Lump sum amount (₹): ", 100000.0)
        rate = get_float("Expected annual return (%) : ", 8.0)
        years = get_int("Period (years): ", 5)
        fv = lump_sum_growth(principal, rate, years)
        print(f"{format_currency(principal)} for {years} years at {rate}% pa -> {format_currency(fv)}")
    print()

def run_retirement_projection(user):
    print("\n--- Retirement Projection ---")
    current = get_float("Current retirement savings (₹): ", user.get("current_savings", 0.0))
    monthly_contrib = get_float("Monthly contribution to retirement (₹): ", 5000.0)
    years = get_int("Years until retirement: ", 20)
    rate = get_float("Expected annual return (%) : ", 8.0)
    corpus = retirement_projection(current, monthly_contrib, years, rate)
    print(f"Estimated retirement corpus in {years} years: {format_currency(corpus)}")
    # simple rule of thumb: 25x annual expenses
    annual_expenses = get_float("Estimate your desired annual retirement expenses (₹): ", 300000.0)
    need = annual_expenses * 25
    print(f"Rule-of-thumb needed corpus (25× annual expenses): {format_currency(need)}")
    if corpus >= need:
        print("Good — projected corpus meets the simple target.")
    else:
        short = need - corpus
        print(f"Shortfall: {format_currency(short)} — consider increasing savings or retirement horizon.")
    print()

def run_tax_estimator(user):
    print("\n--- Tax Estimator (Configurable slabs) ---")
    print("You will provide tax slabs. Example entry: upper_limit rate_percent")
    print("Enter slabs in ascending order. For last slab, enter upper_limit as 'none'.")
    print("Example:")
    print("  250000 0")
    print("  500000 5")
    print("  1000000 20")
    print("  none 30")
    slabs = []
    while True:
        line = input("Enter slab (or blank to finish): ").strip()
        if line == "":
            break
        parts = line.split()
        if len(parts) != 2:
            print("  Please enter exactly two values: upper_limit (or 'none') and rate_percent")
            continue
        up, r = parts
        if up.lower() in ("none", "nil", "rest"):
            up_val = None
        else:
            try:
                up_val = float(up)
            except ValueError:
                print("  Invalid upper_limit. Use a number or 'none'.")
                continue
        try:
            r_val = float(r)
        except ValueError:
            print("  Invalid rate_percent. Use a number like 5 or 20.")
            continue
        slabs.append((up_val, r_val))
    if not slabs:
        print("No slabs entered. Aborting tax estimator.\n")
        return
    income = get_float("Enter your taxable income (₹): ", user.get("annual_income", user.get("monthly_income", 0.0) * 12))
    tax = estimate_tax(income, slabs)
    print(f"Estimated tax on {format_currency(income)} = {format_currency(tax)}\n")

def quick_advice(user):
    # Concise personalized tips
    print("\n--- Quick Personalized Advice ---")
    mi = user.get("monthly_income", 0.0)
    me = user.get("monthly_expenses", 0.0)
    if mi <= 0:
        print("Set up your monthly income in profile for tailored advice.")
    else:
        save = max(0.0, mi - me)
        save_pct = (save / mi * 100) if mi > 0 else 0.0
        print(f"Estimated monthly savings: {format_currency(save)} ({save_pct:.1f}% of income)")
        if save_pct < 10:
            print("Tip: Try to increase savings rate gradually to at least 10-20% of income.")
        elif save_pct < 30:
            print("Good. Aim to automate some investments (SIP / recurring deposit).")
        else:
            print("Great savings rate — consider increasing equity allocation for long-term goals.")
    print("General tips:")
    print(" - Maintain 6 months emergency fund for essentials.")
    print(" - Clear high-interest debt first (credit cards, personal loans).")
    print(" - Diversify: keep some money in liquid cash, some in debt, some in equity for long-term growth.")
    print(" - Review tax-saving opportunities legally available to you each year.\n")

# ---------------- Main loop ----------------
def main():
    print("Welcome to PERSONAL FINANCE CHATBOT — Intelligent guidance for savings, taxes, and investments.")
    user = load_user()
    if user:
        print(f"Hello {user.get('name','there')} — loaded your profile.")
    else:
        print("No profile found. Create one in Setup Profile.")
    while True:
        print("\nMain Menu:")
        print(" 1) Setup / Update Profile")
        print(" 2) Savings projection")
        print(" 3) Emergency fund recommendation")
        print(" 4) Investment projection (SIP / Lump sum)")
        print(" 5) Retirement projection")
        print(" 6) Tax estimator (configurable slabs)")
        print(" 7) Quick personalized advice")
        print(" 8) Save profile & exit")
        print(" 9) Exit without saving")
        choice = input("Choose (1-9): ").strip()
        if choice == "1":
            user = setup_profile(user)
        elif choice == "2":
            run_savings_projection(user)
        elif choice == "3":
            run_emergency_recommendation(user)
        elif choice == "4":
            run_investment_projection(user)
        elif choice == "5":
            run_retirement_projection(user)
        elif choice == "6":
            run_tax_estimator(user)
        elif choice == "7":
            quick_advice(user)
        elif choice == "8":
            save_user(user)
            print("Profile saved. Goodbye!")
            break
        elif choice == "9":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please pick a number 1-9.")

if __name__ == "__main__":
    main()
