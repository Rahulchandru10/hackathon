FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create cache directory for model downloads
RUN mkdir -p /app/.model_cache && chmod 777 /app/.model_cache

# Copy backend package into the /app/backend directory
# so that `import backend.xxx` resolves correctly from WORKDIR /app
COPY . /app/backend

EXPOSE 8000

# Run from /app so that `backend` is a package importable as `backend.xxx`
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
