FROM python:3.6-slim

# Install system dependencies required for OpenCV and scikit-image
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip==21.3.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code into a directory named food_volume_estimation
COPY . /app/food_volume_estimation
WORKDIR /app/food_volume_estimation

# Set PYTHONPATH so absolute imports like 'food_volume_estimation.depth_estimation' work
ENV PYTHONPATH=/app

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
