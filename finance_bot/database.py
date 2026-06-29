from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from finance_bot.config import DATABASE_URL, CA_CERT_PATH
import os

connect_args = {}
if "postgresql" in DATABASE_URL and CA_CERT_PATH and os.path.exists(CA_CERT_PATH):
    connect_args = {
        "sslmode": "require",
        "sslrootcert": CA_CERT_PATH
    }
elif "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    # Import models here to ensure they are registered before creating tables
    import finance_bot.models.transaction
    import finance_bot.models.budget
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
