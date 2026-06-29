from datetime import datetime, timedelta
from sqlalchemy import func
from finance_bot.database import SessionLocal
from finance_bot.models.transaction import Transaction
import csv
import io

def get_daily_report() -> str:
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        # Fetch expenses for today
        expenses = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).filter(
            func.date(Transaction.date) == today,
            Transaction.type == "Expense"
        ).group_by(Transaction.category).all()
        
        if not expenses:
            return "No expenses recorded today."
            
        report = "📅 *Today's Report*\n\n"
        total = 0
        for category, amount in expenses:
            report += f"{category}: ₹{amount:.2f}\n"
            total += amount
            
        report += f"\n*Total*: ₹{total:.2f}"
        return report
    finally:
        db.close()

def get_weekly_report() -> str:
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday()) # Monday
        
        expenses = db.query(Transaction).filter(
            func.date(Transaction.date) >= week_start,
            Transaction.type == "Expense"
        ).all()
        
        if not expenses:
            return "No expenses recorded this week."
            
        total_spent = sum(t.amount for t in expenses)
        # Calculate biggest category and top merchant
        categories = {}
        merchants = {}
        for t in expenses:
            categories[t.category] = categories.get(t.category, 0) + t.amount
            merchants[t.merchant] = merchants.get(t.merchant, 0) + t.amount
            
        biggest_category = max(categories.items(), key=lambda x: x[1]) if categories else ("None", 0)
        top_merchant = max(merchants.items(), key=lambda x: x[1]) if merchants else ("None", 0)
        
        days_passed = today.weekday() + 1
        avg_daily = total_spent / days_passed
        
        report = (
            f"📅 *Weekly Report* (Since Monday)\n\n"
            f"Total spent: ₹{total_spent:.2f}\n"
            f"Biggest category: {biggest_category[0]} (₹{biggest_category[1]:.2f})\n"
            f"Top merchant: {top_merchant[0]} (₹{top_merchant[1]:.2f})\n"
            f"Average daily: ₹{avg_daily:.2f}\n"
        )
        return report
    finally:
        db.close()

def get_monthly_report() -> str:
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)
        
        transactions = db.query(Transaction).filter(
            func.date(Transaction.date) >= month_start
        ).all()
        
        if not transactions:
            return "No transactions recorded this month."
            
        income = sum(t.amount for t in transactions if t.type == "Income")
        expenses = sum(t.amount for t in transactions if t.type == "Expense")
        savings = income - expenses
        
        report = (
            f"📅 *Monthly Report*\n\n"
            f"Income: ₹{income:.2f}\n"
            f"Expenses: ₹{expenses:.2f}\n"
            f"Savings: ₹{savings:.2f}\n"
        )
        return report
    finally:
        db.close()

def generate_csv_export() -> io.StringIO:
    """Exports all transactions to a CSV string buffer."""
    db = SessionLocal()
    try:
        transactions = db.query(Transaction).order_by(Transaction.date.desc()).all()
        output = io.StringIO()
        writer = csv.writer(output)
        
        writer.writerow(['ID', 'Date', 'Merchant', 'Category', 'Subcategory', 'Amount', 'Type', 'Notes'])
        for t in transactions:
            writer.writerow([
                t.id, 
                t.date.strftime("%Y-%m-%d %H:%M:%S"),
                t.merchant,
                t.category,
                t.subcategory,
                t.amount,
                t.type,
                t.notes or ""
            ])
            
        output.seek(0)
        return output
    finally:
        db.close()
