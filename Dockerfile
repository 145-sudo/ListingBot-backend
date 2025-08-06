FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the project into the image
ADD . /app

# Set work directory
WORKDIR /app

RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

RUN uv sync --locked

# Set environment
ENV PATH="/app/.venv/bin:$PATH"
ENV ENVIRONMENT=production

# Expose port
# EXPOSE 8000

# Command to run the app
CMD ["uv", "run", "python", "main.py"]