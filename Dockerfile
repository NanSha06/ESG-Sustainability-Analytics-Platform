FROM python:3.11-slim

# Prevent .pyc files and ensure logs appear immediately in Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first — cached as a separate layer so rebuilds are fast
# when only source code changes (not requirements)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project source
COPY . .

# Ensure the upload directory exists inside the container
RUN mkdir -p data/uploads

# Default command — overridden per-service in docker-compose.yml
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]