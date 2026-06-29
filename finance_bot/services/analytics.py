from finance_bot.database import SessionLocal
from finance_bot.models.transaction import Transaction
from datetime import datetime
import json

def get_transaction_history_json() -> str:
    """
    Extracts all transactions from the database and returns them
    as a JSON string to feed into the AI Financial Advisor.
    """
    db = SessionLocal()
    try:
        transactions = db.query(Transaction).order_by(Transaction.date.desc()).all()
        data = []
        for t in transactions:
            data.append({
                "date": t.date.strftime("%Y-%m-%d"),
                "merchant": t.merchant,
                "category": t.category,
                "amount": t.amount,
                "type": t.type
            })
        return json.dumps(data)
    finally:
        db.close()
