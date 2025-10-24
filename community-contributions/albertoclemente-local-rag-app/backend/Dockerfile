FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps for building and runtime (curl for healthchecks, libmagic for python-magic)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
       git \
       libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md /app/
COPY app /app/app

# Install Python dependencies (editable install to align with dev expectations)
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e .

EXPOSE 8000

ENV HOST=0.0.0.0 \
    PORT=8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
