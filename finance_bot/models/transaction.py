from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from finance_bot.database import Base

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, default=datetime.utcnow, index=True)
    merchant = Column(String, index=True)
    category = Column(String, index=True)
    subcategory = Column(String)
    amount = Column(Float, nullable=False)
    type = Column(String, index=True)  # "Expense" or "Income"
    notes = Column(String, nullable=True)
