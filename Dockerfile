# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# System dependencies (Build essentials)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (Caching optimize karne ke liye)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Environment variable to ensure output is sent to logs
ENV PYTHONUNBUFFERED=1

# Start the bot
CMD ["python3", "main.py"]
