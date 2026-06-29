FROM python:3.11-slim

# Install the ultra-fast uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# Use uv to install dependencies instantly
RUN uv pip install --system -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure start.sh is executable
RUN chmod +x start.sh

# Render provides the PORT environment variable dynamically
ENV PORT=8000

# Start both the bot and the web dashboard
CMD ["bash", "start.sh"]
