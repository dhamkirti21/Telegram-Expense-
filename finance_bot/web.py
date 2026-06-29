from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from datetime import datetime
from sqlalchemy import func
from finance_bot.database import SessionLocal
from finance_bot.models.transaction import Transaction
from telegram import Update
from finance_bot.bot import get_application
import json

# Global reference for the Telegram application
bot_app = get_application()

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

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Receive incoming updates from Telegram"""
    if not bot_app:
        return {"error": "Bot app not initialized"}
        
    # Initialize the app once per Vercel instance if needed
    if not bot_app.bot_data.get("_initialized"):
        await bot_app.initialize()
        bot_app.bot_data["_initialized"] = True
        
    try:
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)
        await bot_app.process_update(update)
        return {"status": "ok"}
    except Exception as e:
        print(f"Error processing webhook: {e}")
        return {"error": str(e)}

@app.get("/set_webhook")
async def set_webhook(url: str):
    """Set the Telegram webhook URL"""
    if not bot_app:
        return {"error": "Bot app not initialized"}
        
    success = await bot_app.bot.set_webhook(url=url)
    if success:
        return {"message": f"Webhook successfully set to {url}"}
    else:
        return {"error": "Failed to set webhook"}
