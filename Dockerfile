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
COPY requirements.txt ./

# Install Python dependencies from requirements to include redis and others
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src ./src

EXPOSE 8000 5678

# Run the application (compose may override to add --reload)
CMD ["uvicorn", "tweetpulse.main:app", "--host", "0.0.0.0"]
