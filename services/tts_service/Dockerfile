FROM python:3.9-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir kafka-python

# Copy application code
COPY . .

# Create output directory if not present (optional)
RUN mkdir -p audio_output

# Run the TTS service
CMD ["python", "main.py"]
