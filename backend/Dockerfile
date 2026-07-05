FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for matplotlib, reportlab, cryptography
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    libffi-dev \
    libssl-dev \
    libfreetype6-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create temp directory
RUN mkdir -p /tmp/naxely

# Create non-root user and grant ownership
RUN useradd -m -u 1000 naxely && chown -R naxely:naxely /app /tmp/naxely
USER naxely

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
