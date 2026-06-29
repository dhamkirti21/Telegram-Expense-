import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://avnadmin:AVNS_2YM5z7k1s0Df0JW72g3@pg-37c4d3c1-dksisodia002-e756.l.aivencloud.com:24944/defaultdb?sslmode=require")
CA_CERT_PATH = os.getenv("CA_CERT_PATH", "/Users/dhamkirtisisodia/Downloads/ca.pem")

# Fix old postgres:// scheme to postgresql:// which SQLAlchemy requires
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ensure required keys are set
if not TELEGRAM_BOT_TOKEN:
    print("Warning: TELEGRAM_BOT_TOKEN is not set.")
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY is not set.")
