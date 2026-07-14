# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for psycopg2 and others
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire src directory
COPY src/ ./src/

# Set Python path so src modules can be resolved
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Command to run the application
CMD uvicorn src.backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
