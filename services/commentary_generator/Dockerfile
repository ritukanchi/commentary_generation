FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir \
    kafka-python \
    pymilvus \
    requests

COPY . .

CMD ["python", "main.py"]
