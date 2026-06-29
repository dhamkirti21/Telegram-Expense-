import matplotlib.pyplot as plt
import io
from finance_bot.database import SessionLocal
from finance_bot.models.transaction import Transaction
from sqlalchemy import func
from datetime import datetime

def generate_monthly_pie_chart() -> io.BytesIO:
    """Generates a pie chart of expenses for the current month and returns it as a BytesIO buffer."""
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)
        
        expenses = db.query(
            Transaction.category,
            func.sum(Transaction.amount).label('total')
        ).filter(
            func.date(Transaction.date) >= month_start,
            Transaction.type == "Expense"
        ).group_by(Transaction.category).all()
        
        if not expenses:
            return None
            
        labels = [e[0] for e in expenses]
        sizes = [e[1] for e in expenses]
        
        plt.figure(figsize=(8, 8))
        
        # Use a modern color map
        colors = plt.cm.Set3(range(len(labels)))
        
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140, colors=colors, wedgeprops={'edgecolor': 'white'})
        plt.title(f"Expenses by Category ({today.strftime('%B %Y')})", fontsize=16, pad=20)
        plt.axis('equal')
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
        buf.seek(0)
        plt.close()
        
        return buf
    finally:
        db.close()
