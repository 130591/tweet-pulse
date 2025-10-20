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

# Install Python dependencies directly
RUN pip install fastapi==0.104.1 uvicorn[standard]==0.24.0 tweepy==4.14.0 \
    sqlalchemy==2.0.23 alembic==1.12.1 psycopg2-binary==2.9.9

# Copy source code
COPY src ./src

EXPOSE 8000 5678

# Run the application (compose may override to add --reload)
CMD ["uvicorn", "tweetpulse.main:app", "--host", "0.0.0.0"]
