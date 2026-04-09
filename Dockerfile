FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies
COPY pyproject.toml .
COPY chatppt/ ./chatppt/
COPY templates/ ./templates/

# Install the application
RUN pip install --no-cache-dir ".[dev]"

# Create directories for artifacts and templates
RUN mkdir -p /app/artifacts /app/templates/default

EXPOSE 8000

CMD ["uvicorn", "chatppt.app.main:create_app", "--host", "0.0.0.0", "--port", "8000"]
