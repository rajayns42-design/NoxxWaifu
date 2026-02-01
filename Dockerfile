# Base image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Environment variable for logs
ENV PYTHONUNBUFFERED=1

# START COMMAND (FIXED: Folder aur file name ke hisaab se)
CMD ["python3", "-m", "NoxxNetwork"]
