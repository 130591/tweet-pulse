# CLI Module

Pulse CLI - Interactive development tool for TweetPulse.

## Module Structure

```
cli/
├── __init__.py     # Package initialization
└── main.py         # Main CLI application
```

## Usage

The CLI can be used in two ways:

### 1. Via wrapper script (recommended)

```bash
python3 pulse.py [command]
```

### 2. As a Python module

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

## Development

To extend the CLI, edit `cli/main.py` and add new commands using the `@app.command()` decorator.

## Dependencies

- typer - CLI framework
- rich - Beautiful terminal output

Install with:
```bash
pip3 install -r requirements-cli.txt
```
