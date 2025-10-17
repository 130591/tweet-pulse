FROM python:3.11-slim

WORKDIR /app

# Install Poetry using pip
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./

# Install dependencies only (not the current project)
RUN poetry install --no-root

# Copy source code
COPY src ./src

EXPOSE 8000

# Run the application
CMD ["poetry", "run", "uvicorn", "src.tweetpulse.main:app", "--host", "0.0.0.0"]
