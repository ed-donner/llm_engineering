# Python services Dockerfile (API Gateway, Streaming Processor, LLM Processor)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster package management
RUN pip install --no-cache-dir uv

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies (minimal set)
RUN uv pip install --system --no-cache -r requirements.txt

# Copy only necessary application code
COPY api_gateway.py streaming_processor.py llm_processor.py ./
COPY database.py models.py redis_client.py ./
COPY setup_database.py ./
COPY utils/ ./utils/

# Expose port for API Gateway
EXPOSE 8000

# Default command (can be overridden in docker-compose)
CMD ["python", "api_gateway.py"]
