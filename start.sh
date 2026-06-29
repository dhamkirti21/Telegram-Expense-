#!/bin/bash

# Start the Telegram bot in the background
python3 -m finance_bot.bot &

# Start the FastAPI web dashboard in the foreground
# Render and Railway will provide the $PORT environment variable automatically
uvicorn finance_bot.web:app --host 0.0.0.0 --port ${PORT:-8000}
