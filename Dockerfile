FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p logs watch_files

# Environment variables
ENV PYTHONUNBUFFERED=1

# Run script
CMD ["python", "scripts/start_monitoring_free.py", "--interval", "15"]
