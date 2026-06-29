from datetime import datetime
from sqlalchemy import func
from finance_bot.database import SessionLocal
from finance_bot.models.budget import Budget
from finance_bot.models.transaction import Transaction

def set_budget(category: str, amount: float) -> str:
    category = category.title()
    db = SessionLocal()
    try:
        budget = db.query(Budget).filter(Budget.category == category).first()
        if budget:
            budget.amount = amount
        else:
            budget = Budget(category=category, amount=amount)
            db.add(budget)
        db.commit()
        return f"✅ Budget set for {category}: ₹{amount:.2f}"
    except Exception as e:
        db.rollback()
        return f"Error setting budget: {e}"
    finally:
        db.close()

def check_budget_status(category: str) -> str:
    """Check budget status for a given category in the current month."""
    category = category.title()
    db = SessionLocal()
    try:
        budget = db.query(Budget).filter(Budget.category == category).first()
        if not budget:
            return "" # No budget set for this category
            
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)
        
        # Calculate total spent in this category this month
        spent = db.query(func.sum(Transaction.amount)).filter(
            Transaction.category == category,
            Transaction.type == "Expense",
            func.date(Transaction.date) >= month_start
        ).scalar() or 0.0
        
        percentage = (spent / budget.amount) * 100 if budget.amount > 0 else 0
        remaining = budget.amount - spent
        
        warning_msg = ""
        if percentage >= 100:
            warning_msg = f"\n⚠️ *BUDGET EXCEEDED* for {category}!"
        elif percentage >= 90:
            warning_msg = f"\n⚠️ *WARNING*: 90% of {category} budget reached."
        elif percentage >= 80:
            warning_msg = f"\n⚠️ *WARNING*: 80% of {category} budget reached."
            
        if warning_msg:
            return f"{warning_msg}\nRemaining: ₹{remaining:.2f} of ₹{budget.amount:.2f}"
            
        return ""
    finally:
        db.close()

def get_all_budgets() -> str:
    db = SessionLocal()
    try:
        budgets = db.query(Budget).all()
        if not budgets:
            return "No budgets configured."
            
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)
        
        report = "📊 *Budget Status*\n\n"
        for b in budgets:
            spent = db.query(func.sum(Transaction.amount)).filter(
                Transaction.category == b.category,
                Transaction.type == "Expense",
                func.date(Transaction.date) >= month_start
            ).scalar() or 0.0
            
            remaining = b.amount - spent
            report += f"*{b.category}*: ₹{spent:.2f} / ₹{b.amount:.2f} (Remaining: ₹{remaining:.2f})\n"
            
        return report
    finally:
        db.close()
