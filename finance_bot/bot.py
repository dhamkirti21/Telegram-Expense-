import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from finance_bot.config import TELEGRAM_BOT_TOKEN
from finance_bot.database import init_db, SessionLocal
from finance_bot.models.transaction import Transaction
from finance_bot.utils.parser import parse_transaction_locally
from finance_bot.services.groq_service import categorize_transaction, get_financial_advice
from finance_bot.services.reports import get_daily_report, get_weekly_report, get_monthly_report, generate_csv_export
from finance_bot.services.budget import set_budget, check_budget_status, get_all_budgets
from finance_bot.services.analytics import get_transaction_history_json
from finance_bot.utils.charts import generate_monthly_pie_chart

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hello! I am your Personal AI Finance Bot.\n"
        "Just type your expenses naturally (e.g., 'zomato 350' or 'salary 25000').\n"
        "Use /help to see available commands."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "Available Commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/today - Show today's report\n"
        "/stats - General stats (coming soon)\n\n"
        "Just type an expense naturally, e.g., 'uber 150'"
    )
    await update.message.reply_text(help_text)

async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_daily_report(), parse_mode='Markdown')

async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_weekly_report(), parse_mode='Markdown')

async def month_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_monthly_report(), parse_mode='Markdown')

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_all_budgets(), parse_mode='Markdown')

async def budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /budget <category> <amount>\nExample: /budget food 5000")
        return
    category = args[0]
    try:
        amount = float(args[1])
        reply = set_budget(category, amount)
        await update.message.reply_text(reply)
    except ValueError:
        await update.message.reply_text("Amount must be a number.")

async def chart_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buf = generate_monthly_pie_chart()
    if buf:
        await update.message.reply_photo(photo=buf, caption="Here is your monthly spending breakdown!")
    else:
        await update.message.reply_text("Not enough data to generate a chart this month.")

async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    csv_file = generate_csv_export()
    import io
    bytes_io = io.BytesIO(csv_file.getvalue().encode('utf-8'))
    bytes_io.name = "expenses_export.csv"
    await update.message.reply_document(document=bytes_io, filename="expenses_export.csv", caption="Here is your complete transaction history.")

async def dashboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db = SessionLocal()
    try:
        recent_txs = db.query(Transaction).order_by(Transaction.date.desc()).limit(15).all()
        if not recent_txs:
            await update.message.reply_text("No transactions found.")
            return

        table = "📊 *Recent Transactions Dashboard*\n\n```text\n"
        table += f"{'Date':<11} | {'Merchant':<12} | {'Amount':>8}\n"
        table += "-" * 37 + "\n"
        
        for tx in recent_txs:
            date_str = tx.date.strftime('%m-%d')
            merchant = tx.merchant[:12] if len(tx.merchant) > 12 else tx.merchant
            sign = "+" if tx.type == "Income" else "-"
            amt = f"{sign}{tx.amount:.0f}"
            table += f"{date_str:<11} | {merchant:<12} | {amt:>8}\n"
            
        table += "```\n\n🌐 For the full interactive dashboard, ensure `uvicorn finance_bot.web:app` is running and open http://localhost:8000"
        await update.message.reply_text(table, parse_mode='Markdown')
    finally:
        db.close()

async def advice_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("🤔 Analyzing your transactions to generate savings advice... This might take a few seconds.")
    history_json = get_transaction_history_json()
    if history_json == "[]":
        await msg.edit_text("You don't have any transactions yet to analyze!")
        return
        
    prompt = "Please give me a comprehensive analysis of my spending, identify patterns, and provide actionable advice on how I can save money and improve my usage of money."
    reply = get_financial_advice(history_json, prompt)
    await msg.edit_text(reply, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    # 0. Check if it's a question for the AI Advisor
    text_lower = text.lower()
    if "?" in text_lower or text_lower.startswith(("how", "show", "what", "top", "give", "analyze")):
        msg = await update.message.reply_text("🤔 Analyzing your finances...")
        history_json = get_transaction_history_json()
        reply = get_financial_advice(history_json, text)
        await msg.edit_text(reply, parse_mode='Markdown')
        return

    # 1. Try local parsing first (fast path, no API call)
    transaction_data = parse_transaction_locally(text)
    
    if not transaction_data:
        # 2. Fallback to Groq API
        logger.info(f"Falling back to Groq for text: {text}")
        transaction_data = categorize_transaction(text)
        
    if not transaction_data:
        await update.message.reply_text("Sorry, I couldn't understand that transaction. Please try again.")
        return
        
    # 3. Save to database
    db = SessionLocal()
    try:
        new_tx = Transaction(
            merchant=transaction_data.get("merchant", "Unknown"),
            category=transaction_data.get("category", "Miscellaneous"),
            subcategory=transaction_data.get("subcategory", ""),
            amount=transaction_data.get("amount", 0.0),
            type=transaction_data.get("type", "Expense")
        )
        db.add(new_tx)
        db.commit()
        
        # 4. Reply to user
        icon = "📉" if new_tx.type == "Expense" else "📈"
        reply_msg = (
            f"✅ Recorded!\n"
            f"{icon} {new_tx.category} | {new_tx.merchant}\n"
            f"₹{new_tx.amount}"
        )
        # 4. Check budget
        budget_warning = check_budget_status(new_tx.category)
        if budget_warning:
            reply_msg += "\n" + budget_warning
            
        await update.message.reply_text(reply_msg)
        
    except Exception as e:
        logger.error(f"Error saving to database: {e}")
        await update.message.reply_text("Error saving transaction.")
    finally:
        db.close()

def main():
    # Initialize the database
    init_db()
    
    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN is missing! Please set it in .env")
        return

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(CommandHandler('today', today_command))
    application.add_handler(CommandHandler('week', week_command))
    application.add_handler(CommandHandler('month', month_command))
    application.add_handler(CommandHandler('stats', stats_command))
    application.add_handler(CommandHandler('budget', budget_command))
    application.add_handler(CommandHandler('chart', chart_command))
    application.add_handler(CommandHandler('export', export_command))
    application.add_handler(CommandHandler('dashboard', dashboard_command))
    application.add_handler(CommandHandler('advice', advice_command))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot is starting up...")
    application.run_polling()

if __name__ == '__main__':
    main()
