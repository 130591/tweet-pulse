cat > README.md << 'EOF'
# TweetPulse - Real-time Social Intelligence Platform

## Overview

TweetPulse é uma plataforma de análise de tweets em tempo real que demonstra padrões profissionais de desenvolvimento Python para web e data engineering.

## Quick Start

### Pré-requisitos

- Python 3.11+
- Poetry
- PostgreSQL
- Redis
- Docker (opcional)

### Setup Local
```bash
# Clone o repositório
git clone https://github.com/username/tweetpulse.git
cd tweetpulse

# Instale dependências
poetry install

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais

# Rode migrações
poetry run alembic upgrade head

# Inicie a aplicação
poetry run uvicorn src.tweetpulse.main:app --reload --host 0.0.0.0 --port 8000

# Em outro terminal, inicie Celery worker
poetry run celery -A src.tweetpulse.worker.celery_app worker -l info
```

### Com Docker
```bash
docker-compose up -d
```

## Estrutura do Projeto