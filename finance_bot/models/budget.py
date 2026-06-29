from sqlalchemy import Column, Integer, String, Float
from finance_bot.database import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, unique=True, index=True)
    amount = Column(Float, nullable=False)
