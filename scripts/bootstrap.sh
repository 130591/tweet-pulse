#!/bin/bash
# bootstrap.sh - Inicializa projeto TweetPulse

set -e

echo "=== TweetPulse Bootstrap ==="

# Check Python version
if ! command -v python3.11 &> /dev/null; then
    echo "Python 3.11+ required"
    exit 1
fi

# Install Poetry if not present
if ! command -v poetry &> /dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

# Create structure
echo "Creating directory structure..."
mkdir -p src/tweetpulse/{core,api,services,models,database,cache,ml,worker,utils}
mkdir -p tests/{test_api,test_services,test_ml,test_integration,fixtures}
mkdir -p infrastructure/{kubernetes,terraform,monitoring}
mkdir -p scripts docs

# Generate files
echo "Generating config files..."
poetry install

# Database setup
echo "Setting up database..."
poetry run alembic upgrade head

# Create pre-commit hooks
echo "Setting up pre-commit hooks..."
poetry run pre-commit install

echo "=== Setup Complete ==="
echo "Next steps:"
echo "1. Edit .env with your credentials"
echo "2. Run: poetry run uvicorn src.tweetpulse.main:app --reload"