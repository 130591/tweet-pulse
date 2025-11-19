# CLI Module

Pulse CLI - Interactive development tool for TweetPulse.

## 🐳 Docker-First Approach

**Important:** This CLI is designed to run **inside Docker containers** to ensure all dependencies remain containerized. The CLI does not install dependencies on the host system.

## Module Structure

```
cli/
├── __init__.py     # Package initialization
└── main.py         # Main CLI application
```

## Usage

### 1. Via wrapper script (recommended)

```bash
./pulse [command]
```

The wrapper automatically:
- Checks if Docker is running
- Starts required services (db, redis) if needed
- Executes the CLI inside the Docker container
- Keeps all dependencies containerized

### 2. Direct Docker execution

```bash
docker-compose -f docker-compose-dev.yml run --rm app python3 cli/src/main.py [command]
```

### 3. As a Python module (inside container)

```python
from cli.main import app

if __name__ == "__main__":
    app()
```

## Commands

- `interactive` - Interactive mode with menu
- `dev [service]` - Start development services
- `stop` - Stop all services
- `status` - Show services status
- `logs` - Show service logs
- `clean` - Clean Docker environment
- `rebuild` - Rebuild Docker images

## Services

- `worker` - Tweet processing worker
- `backend` - FastAPI backend server
- `frontend` - React frontend
- `api` - Workers + Backend
- `all` - Full environment (all services + frontend)

## Dependencies

All CLI dependencies are included in `requirements-lite.txt` and installed inside the container:

- typer - CLI framework
- rich - Beautiful terminal output

**No host system installation required** - dependencies stay fully containerized.

## Development

To extend the CLI, edit `cli/main.py` and add new commands using the `@app.command()` decorator.
