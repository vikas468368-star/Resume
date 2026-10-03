FROM python:3.11-slim

# Avoid prompts from debian frontend
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies for OCR (Tesseract) and PDF rendering (Poppler)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m spacy download en_core_web_sm

# Copy project files
COPY . .

# Seed initial database
RUN python seed.py

ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

# Start Gunicorn server
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120"]
