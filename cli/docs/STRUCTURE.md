# CLI Module Structure

## Overview

The Pulse CLI is now organized as a proper Python module with all text in English.

## Directory Structure

```
tweet-pulse/
├── cli/                      # CLI module package
│   ├── __init__.py          # Package initialization, exports app and main
│   ├── main.py              # Main CLI application (all commands)
│   ├── README.md            # Module documentation
│   └── STRUCTURE.md         # This file
├── pulse.py                 # Wrapper script (imports cli.main)
├── requirements-cli.txt     # CLI dependencies (typer, rich)
├── install-cli.sh           # Installation script
├── CLI_README.md            # Complete CLI documentation
└── QUICK_START.md           # Quick start guide
```

## Module Components

### `cli/__init__.py`
- Package initialization
- Exports `app` (Typer application)
- Exports `main` function

### `cli/main.py`
- Main CLI application
- All commands implementation:
  - `interactive` - Interactive menu
  - `dev` - Start services
  - `stop` - Stop services
  - `status` - Show status
  - `logs` - Show logs
  - `clean` - Clean environment
  - `rebuild` - Rebuild images
- Service definitions
- Helper functions

### `pulse.py` (wrapper)
- Simple wrapper script
- Imports `cli.main.app`
- Executable entry point

## Usage

### As a module
```python
from cli.main import app

if __name__ == "__main__":
    app()
```

### Via wrapper
```bash
python3 pulse.py [command]
./pulse.py [command]
```

## Language

All text in the CLI is in English:
- Command names and descriptions
- Help messages
- Console output
- Error messages
- Interactive prompts

## Dependencies

- **typer** - CLI framework with type hints
- **rich** - Beautiful terminal formatting

## Adding New Commands

To add new commands, edit `cli/main.py`:

```python
@app.command()
def mycommand(
    arg: str = typer.Argument(..., help="Description")
):
    """Command description"""
    console.print("[green]Executing command...[/green]")
    # Implementation here
```

## Module Import

The module is imported in `pulse.py` like this:

```python
from cli.main import app

if __name__ == "__main__":
    app()
```

This allows the CLI to be:
1. Run directly: `python3 pulse.py`
2. Imported as a module: `from cli.main import app`
3. Distributed as a package

## Benefits of Module Structure

1. **Better organization** - Clear separation of concerns
2. **Reusability** - Can be imported in other scripts
3. **Testability** - Easy to write unit tests
4. **Maintainability** - Clear module boundaries
5. **Scalability** - Easy to add new features

## Future Enhancements

- Split commands into separate files (e.g., `cli/commands/dev.py`)
- Add configuration file support
- Add plugin system
- Create standalone executable with PyInstaller
