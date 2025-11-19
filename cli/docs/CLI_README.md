# Pulse CLI - TweetPulse Control Tool

An interactive and beautiful CLI tool to manage your TweetPulse development environment.

> **Note:** The CLI is now organized as a Python module in the `cli/` directory.

## Setup

To make it easier to run the CLI, you can create an alias in your shell:

```bash
alias pulse='python3 /home/evertonpaixao/projects/tweet-pulse/pulse.py'
```

Then you can run the CLI with just `pulse`.

Alternatively, you can add the alias to your shell configuration file for a more permanent solution. Here's how:

### For Bash users

Add the following line to your `~/.bashrc` file:

```bash
alias pulse='python3 /home/evertonpaixao/projects/tweet-pulse/pulse.py'
```

Then, reload your shell configuration by running:

```bash
source ~/.bashrc
```

### For Zsh users

Add the following line to your `~/.zshrc` file:

```bash
alias pulse='python3 /home/evertonpaixao/projects/tweet-pulse/pulse.py'
```

Then, reload your shell configuration by running:

```bash
source ~/.zshrc
```

## Installation

```bash
# Install dependencies
pip3 install -r requirements-cli.txt

# Make executable (already done)
chmod +x pulse.py
```

## Module Structure

The CLI is organized as a Python module:

```
cli/
├── __init__.py     # Package initialization
├── main.py         # Main CLI application
└── README.md       # Module documentation
```

The `pulse.py` file at the project root is a simple wrapper that imports and runs the CLI module.

## How to Use

### Interactive Mode (Recommended)

```bash
python3 pulse.py
```

The interactive mode will ask you:
1. Which service to run (worker, backend, frontend, api, all)
2. Which version to use (Lite or Full) - **only for Docker services** (worker, backend, api, all)

**Note:** Frontend runs standalone with npm and doesn't require version selection.

### Direct Commands

```bash
# Run everything with LITE version (default, ~500MB)
python3 pulse.py dev all

# Run everything with FULL version (with ML models, ~3.5GB)
python3 pulse.py dev all --full

# Run only frontend
python3 pulse.py dev frontend

# Check status
python3 pulse.py status

# Run in background (detached)
python3 pulse.py dev all -d

# Rebuild and run
python3 pulse.py dev all -b
```

### Lite vs Full Mode

**Applies only to:** worker, backend, api, and all services

- **Lite Mode** (default): Uses `docker-compose-dev.yml` (~500MB)
  - Faster startup
  - Less memory usage
  - Perfect for development
  - No heavy ML models
  
- **Full Mode** (--full flag): Uses `docker-compose.yml` (~3.5GB)
  - Full sentiment analysis with ML models
  - All ML features
  - Use for production-like testing

**Service Isolation:**
- **Frontend**: Runs standalone with npm/Vite (no Docker required, no version selection)
- **Docker services**: Worker, backend, api, and all options run in Docker containers

### Compose Files Used

- `docker-compose-dev.yml` → **Lite mode** (default for development)
- `docker-compose.yml` → **Full mode** (complete with ML)

### Available Commands

#### Start Services

```bash
# Run only the worker
./pulse.py dev worker

# Run only the backend
./pulse.py dev backend

# Run only the frontend
./pulse.py dev frontend

# Run workers + backend (complete API)
./pulse.py dev api

# Run everything (backend + workers + frontend)
./pulse.py dev all

# Run in background (detached)
./pulse.py dev all -d

# Run with rebuild
./pulse.py dev all -b
```

#### Stop Services

```bash
./pulse.py stop
```

#### Show Status

```bash
./pulse.py status
```

#### Show Logs

```bash
# Show all logs
./pulse.py logs

# Show logs from a specific service
./pulse.py logs worker

# Follow logs in real-time
./pulse.py logs -f

# Show last 50 lines
./pulse.py logs --tail 50
```

#### Clean Environment

```bash
# Clean only containers
./pulse.py clean

# Clean containers and volumes
./pulse.py clean --volumes

# Clean containers and images
./pulse.py clean --images

# Clean everything (containers + volumes + images)
./pulse.py clean --all
```

#### Rebuild Images

```bash
# Rebuild all images
./pulse.py rebuild

# Rebuild specific service
./pulse.py rebuild worker
```

## Features

- Beautiful and colorful interface with Rich
- Interactive mode with selection menu
- Direct commands for fast development
- Real-time status visualization
- Log management
- Easy environment cleanup
- Simplified rebuild
- Granular service control

## Available Services

| Command | Service | Description | Version Choice |
|---------|---------|-------------|----------------|
| `worker` | Worker | Processes tweets from Kafka | Yes (Lite/Full) |
| `backend` | Backend API | FastAPI server | Yes (Lite/Full) |
| `frontend` | Frontend | React interface (npm) | **No** |
| `api` | Complete API | Workers + Backend | Yes (Lite/Full) |
| `all` | Full Environment | All services + Frontend | Yes (Lite/Full) |

## Tips

### Create shell alias

Add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias pulse='python3 /home/evertonpaixao/projects/tweet-pulse/pulse.py'
```

Then you can simply use:

```bash
pulse
pulse dev frontend
pulse status
```

### Recommended Workflow

```bash
# 1. Start everything in development
pulse dev all

# 2. View logs in another window
pulse logs -f

# 3. Check status
pulse status

# 4. Stop when finished
pulse stop
```

## Troubleshooting

### Docker won't start

The CLI tries to start Docker automatically. If it fails:

```bash
sudo service docker start
```

### Ports in use

```bash
# Stop everything first
pulse stop

# Clean environment
pulse clean

# Try again
pulse dev all
```

### Rebuild needed

If there are code changes or Dockerfile updates:

```bash
pulse rebuild
pulse dev all
```

## Usage Examples

### Frontend Development

```bash
# Only frontend to develop UI (no Docker, runs with npm)
pulse dev frontend

# Frontend runs at http://localhost:5173
# No version selection needed - it's just the React app
```

### Backend Development

```bash
# Backend + workers to test API
pulse dev api
```

### Full Test

```bash
# Everything running
pulse dev all -d

# Check if everything started
pulse status

# View logs
pulse logs -f
```

### Clean and Restart

```bash
# Stop everything
pulse stop

# Clean completely
pulse clean --all

# Rebuild from scratch
pulse rebuild

# Start again
pulse dev all
```

## Next Features (TODO)

- [ ] `pulse prod` command for production
- [ ] Test integration
- [ ] Automated health checks
- [ ] Volume backups
- [ ] Resource monitoring
- [ ] Automated deployment

---

Made with for TweetPulse
