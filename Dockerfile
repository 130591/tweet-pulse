FROM python:3.11-slim

WORKDIR /app

# Environment tweaks for reliable Docker builds and debugging
ENV POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

# Install Poetry and debugpy using pip
RUN pip install --no-cache-dir poetry debugpy

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies only (not the current project)
RUN poetry install --no-root

# Copy source code
COPY src ./src

EXPOSE 8000 5678

# Run the application (compose may override to add --reload)
CMD ["poetry", "run", "uvicorn", "tweetpulse.main:app", "--host", "0.0.0.0"]
