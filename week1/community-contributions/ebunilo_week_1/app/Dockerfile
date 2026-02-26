# Company Brochure Generator - Docker image for private cloud
FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck (optional; remove and use CMD-SHELL with python if you prefer)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY scraper.py brochure.py main.py ./

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

ENV PORT=8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
