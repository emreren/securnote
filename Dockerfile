FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Configure poetry
RUN poetry config virtualenvs.create false

# Install dependencies without installing the project
RUN poetry install --only=main --no-root

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p data

# Expose port for test API only
EXPOSE 8000

# Run the test API (minimal interface)
CMD ["python", "scripts/run_web.py"]