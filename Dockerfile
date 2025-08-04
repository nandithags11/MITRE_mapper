# Use an official Python image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy your project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Set environment variables (optional; use .env for secrets)
ENV PYTHONUNBUFFERED=1

# Entry point (optional)
CMD ["python", "upload_log.py", "path/to/nginx.log"]
