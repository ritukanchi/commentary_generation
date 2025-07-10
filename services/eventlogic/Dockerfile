FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (for logging and basic functionality)
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir kafka-python

# Copy application code
COPY . .

# Run the service
CMD ["python", "main.py"]
