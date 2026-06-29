from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from datetime import datetime
from sqlalchemy import func
from finance_bot.database import SessionLocal
from finance_bot.models.transaction import Transaction

app = FastAPI(title="Personal Finance Dashboard")

# Set up templates directory
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    db = SessionLocal()
    try:
        today = datetime.utcnow().date()
        month_start = today.replace(day=1)

        # Aggregate current month data
        income = db.query(func.sum(Transaction.amount)).filter(
            func.date(Transaction.date) >= month_start,
            Transaction.type == "Income"
        ).scalar() or 0.0

        expense = db.query(func.sum(Transaction.amount)).filter(
            func.date(Transaction.date) >= month_start,
            Transaction.type == "Expense"
        ).scalar() or 0.0

        # Get top 5 recent transactions
        recent_txs = db.query(Transaction).order_by(Transaction.date.desc()).limit(10).all()

        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "request": request,
                "month": today.strftime("%B %Y"),
                "income": income,
                "expense": expense,
                "savings": income - expense,
                "transactions": recent_txs
            }
        )
    finally:
        db.close()
