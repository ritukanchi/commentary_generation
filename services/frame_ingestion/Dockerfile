FROM python:3.9-slim

WORKDIR /app

# Install system dependencies required by OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install only needed Python packages directly

# Copy your Python script(s)
COPY . .

# Run your frame ingestion service
CMD ["python", "main.py"]
