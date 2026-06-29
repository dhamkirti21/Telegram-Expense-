import sys
import os

# Add the project directory to path so we can import finance_bot
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from finance_bot.database import SessionLocal
from finance_bot.models.transaction import Transaction

def clear_database():
    db = SessionLocal()
    try:
        deleted_count = db.query(Transaction).delete()
        db.commit()
        print(f"✅ Successfully deleted {deleted_count} transactions from the database.")
    except Exception as e:
        print(f"❌ Error clearing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    confirm = input("⚠️ Are you sure you want to completely clear ALL transactions from your cloud database? (y/n): ")
    if confirm.lower() == 'y':
        clear_database()
    else:
        print("Operation cancelled.")
