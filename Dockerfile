FROM python:3.12-slim

# Install uv (if using pyproject.toml and uv for dependency management)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the project into the image
ADD . /app

# Set work directory
WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Install dependencies with uv (if using pyproject.toml)
RUN uv sync --locked

# Install uvicorn (if not already in pyproject.toml)
RUN uv pip install uvicorn

# Expose the port FastAPI will run on
EXPOSE 8000

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV ENVIRONMENT=production
# Set default DATABASE_URL but allow override from Railway.app
ENV DATABASE_URL=${DATABASE_URL}

RUN uv run seeder.py

# Run FastAPI app with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
