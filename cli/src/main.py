#!/usr/bin/env python3
"""
🌊 Pulse CLI - TweetPulse Development Tool
An interactive tool to manage your TweetPulse development environment
"""

import subprocess
import sys
import os
from typing import Optional, List
from pathlib import Path

try:
	import typer
	from rich.console import Console
	from rich.panel import Panel
	from rich.prompt import Confirm, Prompt
	from rich.table import Table
	from rich import box
	from rich.live import Live
	from rich.spinner import Spinner
except ImportError:
	print("❌ Dependencies not found. Installing...")
	subprocess.run([sys.executable, "-m", "pip", "install", "typer", "rich"], check=True)
	import typer
	from rich.console import Console
	from rich.panel import Panel
	from rich.prompt import Confirm, Prompt
	from rich.table import Table
	from rich import box
	from rich.live import Live
	from rich.spinner import Spinner

app = typer.Typer(
    name="pulse",
    help="🌊 TweetPulse CLI - Control your development environment",
    add_completion=False,
)
console = Console()

# Service definitions
SERVICES = {
    "worker": {
        "name": "Worker",
        "emoji": "⚙️",
        "compose": ["redis", "db", "worker"],
        "description": "Processes tweets from Kafka"
    },
    "backend": {
        "name": "Backend API",
        "emoji": "🚀",
        "compose": ["db", "redis", "app"],
        "description": "FastAPI server"
    },
    "frontend": {
        "name": "Frontend",
        "emoji": "💻",
        "compose": [],  # Frontend runs with npm
        "description": "React interface"
    },
    "api": {
        "name": "Complete API",
        "emoji": "🔥",
        "compose": ["redis", "db", "worker", "app"],
        "description": "Workers + Backend"
    },
    "all": {
        "name": "Full Environment",
        "emoji": "🌊",
        "compose": ["redis", "db", "worker", "app"],
        "description": "All services + Frontend"
    }
}


def run_command(cmd: List[str], cwd: Optional[Path] = None, check: bool = True) -> subprocess.CompletedProcess:
	"""Execute command and return result"""
	return subprocess.run(cmd, cwd=cwd, check=check, capture_output=False)


def check_docker():
	"""Check if Docker is running"""
	try:
			subprocess.run(
				["docker", "ps"],
				check=True,
				stdout=subprocess.DEVNULL,
				stderr=subprocess.DEVNULL
			)
			return True
	except subprocess.CalledProcessError:
			return False


def start_docker():
    """Start Docker daemon"""
    console.print("[yellow]🐳 Starting Docker...[/yellow]")
    try:
        subprocess.run(["sudo", "service", "docker", "start"], check=True, capture_output=True)
        console.print("[green]✓ Docker started successfully![/green]")
        return True
    except subprocess.CalledProcessError as e:
        console.print(f"[red]✗ Error starting Docker: {e}[/red]")
        return False


def get_active_compose_file():
    """Detect which compose file has running containers"""
    # Try dev first (more common)
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose-dev.yml", "ps", "-q"],
        capture_output=True,
        text=True
    )
    if result.stdout.strip():
        return "docker-compose-dev.yml"
    
    # Try full
    result = subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "ps", "-q"],
        capture_output=True,
        text=True
    )
    if result.stdout.strip():
        return "docker-compose.yml"
    
    # Default to dev if nothing running
    return "docker-compose-dev.yml"


def show_banner():
	"""Show CLI banner"""
	banner = """
	╔══════════════════════════════════════╗
	║   🌊  PULSE CLI - TweetPulse  🌊    ║
	║   Full Control of Your Project       ║
	╚══════════════════════════════════════╝
	"""
	console.print(Panel(banner, style="bold cyan", box=box.DOUBLE))


def show_services_menu():
	"""Show available services menu"""
	table = Table(title="📋 Available Services", box=box.ROUNDED, show_header=True, header_style="bold magenta")
	table.add_column("Command", style="cyan", no_wrap=True)
	table.add_column("Service", style="green")
	table.add_column("Description", style="white")
	
	for key, service in SERVICES.items():
		table.add_row(
			f"pulse dev {key}",
			f"{service['emoji']} {service['name']}",
			service['description']
	  )
	
	console.print(table)


@app.command()
def interactive():
    """🎯 Interactive mode - choose what to run"""
    show_banner()
    
    # Check Docker
    if not check_docker():
        console.print("[yellow]⚠️  Docker is not running[/yellow]")
        if Confirm.ask("Would you like to start Docker?"):
            if not start_docker():
                raise typer.Exit(1)
        else:
            console.print("[red]Docker is required to run services[/red]")
            raise typer.Exit(1)
    
    # Services menu
    console.print("\n[bold]Choose what you want to run:[/bold]\n")
    
    choices = []
    for idx, (key, service) in enumerate(SERVICES.items(), 1):
        console.print(f"  {idx}. {service['emoji']} [cyan]{service['name']}[/cyan] - {service['description']}")
        choices.append(key)
    
    console.print(f"  {len(choices) + 1}. ❌ Stop everything")
    console.print(f"  {len(choices) + 2}. 🚪 Exit\n")
    
    choice = Prompt.ask(
        "Your choice",
        choices=[str(i) for i in range(1, len(choices) + 3)],
        default="5"
    )
    
    choice_idx = int(choice) - 1
    
    if choice_idx == len(choices):  # Stop everything
        stop()
    elif choice_idx == len(choices) + 1:  # Exit
        console.print("[yellow]👋 Goodbye![/yellow]")
        raise typer.Exit(0)
    else:
        service_key = choices[choice_idx]
        
        # Ask about lite vs full mode
        console.print("\n[bold]Choose version:[/bold]")
        console.print("  1. 🪶 [cyan]Lite[/cyan] - Optimized, ~500MB (recommended for dev)")
        console.print("  2. 🚀 [cyan]Full[/cyan] - With ML models, ~3.5GB\n")
        
        version_choice = Prompt.ask("Your choice", choices=["1", "2"], default="1")
        full_mode = version_choice == "2"
        
        version_name = "FULL" if full_mode else "LITE"
        console.print(f"\n[cyan]📦 Mode: {version_name}[/cyan]")
        console.print(f"[green]🚀 Starting {SERVICES[service_key]['name']}...[/green]\n")
        _start_service(service_key, full_mode=full_mode)


@app.command()
def dev(
    service: str = typer.Argument(
        "all",
        help="Service to run: worker, backend, frontend, api, all"
    ),
    detach: bool = typer.Option(False, "--detach", "-d", help="Run in background"),
    build: bool = typer.Option(False, "--build", "-b", help="Rebuild images"),
    full: bool = typer.Option(False, "--full", "-f", help="Use full version (with ML models). Default: lite version"),
):
    """🚀 Start development environment (uses lite version by default)"""
    
    if service not in SERVICES:
        console.print(f"[red]❌ Service '{service}' does not exist[/red]\n")
        show_services_menu()
        raise typer.Exit(1)
    
    # Check Docker
    if not check_docker():
        console.print("[yellow]⚠️  Docker is not running. Starting...[/yellow]")
        if not start_docker():
            raise typer.Exit(1)
    
    # Show version info
    version_mode = "FULL (with ML models)" if full else "LITE (optimized, ~500MB)"
    console.print(f"[cyan]📦 Mode: {version_mode}[/cyan]")
    console.print(f"[green]🚀 Starting {SERVICES[service]['emoji']} {SERVICES[service]['name']}...[/green]\n")
    
    _start_service(service, detach=detach, build=build, full_mode=full)


def _start_service(service: str, detach: bool = False, build: bool = False, full_mode: bool = False):
    """Start a specific service"""
    config = SERVICES[service]
    
    try:
        # For Docker Compose services
        if config["compose"]:
            cmd = ["docker", "compose"]
            
            # Use dev compose (lite) by default, full if specified
            if not full_mode:
                cmd.extend(["-f", "docker-compose-dev.yml"])
                console.print("[dim]Using lite compose (docker-compose-dev.yml)[/dim]")
            else:
                cmd.extend(["-f", "docker-compose.yml"])
                console.print("[dim]Using full compose (docker-compose.yml)[/dim]")
            
            cmd.append("up")
            
            if detach:
                cmd.append("-d")
            
            if build:
                cmd.append("--build")
            
            cmd.extend(config["compose"])
            
            console.print(f"[dim]Executing: {' '.join(cmd)}[/dim]\n")
            run_command(cmd)
        
        # If frontend or all, run npm
        if service in ["frontend", "all"]:
            frontend_path = Path.cwd() / "frontend"
            if frontend_path.exists():
                console.print("\n[cyan]💻 Starting Frontend...[/cyan]")
                
                # Check if node_modules exists
                if not (frontend_path / "node_modules").exists():
                    console.print("[yellow]📦 Installing frontend dependencies...[/yellow]")
                    run_command(["npm", "install"], cwd=frontend_path)
                
                if service == "all" or detach:
                    # Run in background
                    console.print("[green]Frontend running at http://localhost:5173[/green]")
                    subprocess.Popen(["npm", "run", "dev"], cwd=frontend_path)
                else:
                    # Run in foreground
                    run_command(["npm", "run", "dev"], cwd=frontend_path)
            else:
                console.print("[yellow]⚠️  Frontend directory not found[/yellow]")
        
        if not detach:
            console.print("\n[green]✓ Services started![/green]")
            console.print("[dim]Press Ctrl+C to stop[/dim]")
        else:
            console.print("\n[green]✓ Services running in background![/green]")
            console.print("[dim]Use 'pulse stop' to stop them[/dim]")
            
    except KeyboardInterrupt:
        console.print("\n[yellow]🛑 Stopping services...[/yellow]")
        stop()
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Error starting service: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def stop():
    """🛑 Stop all services"""
    console.print("[yellow]🛑 Stopping all services...[/yellow]\n")
    
    try:
        # Stop both compose files (dev and full) to ensure everything stops
        run_command(["docker", "compose", "-f", "docker-compose-dev.yml", "down"], check=False)
        run_command(["docker", "compose", "-f", "docker-compose.yml", "down"], check=False)
        console.print("[green]✓ Docker services stopped[/green]")
        
        # Stop Node processes (frontend)
        try:
            subprocess.run(["pkill", "-f", "vite"], check=False, capture_output=True)
            console.print("[green]✓ Frontend stopped[/green]")
        except:
            pass
        
        console.print("\n[green]✓ All services stopped![/green]")
    except Exception as e:
        console.print(f"[red]❌ Error stopping services: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def status():
    """📊 Show services status"""
    console.print("[bold]📊 Services Status[/bold]\n")
    
    try:
        compose_file = get_active_compose_file()
        mode = "LITE (dev)" if "dev" in compose_file else "FULL"
        console.print(f"[dim]Active mode: {mode}[/dim]\n")
        
        result = subprocess.run(
            ["docker", "compose", "-f", compose_file, "ps", "--format", "json"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout.strip():
            import json
            containers = [json.loads(line) for line in result.stdout.strip().split('\n')]
            
            table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
            table.add_column("Service", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Ports")
            
            for container in containers:
                status_color = "green" if container.get("State") == "running" else "red"
                table.add_row(
                    container.get("Service", "N/A"),
                    f"[{status_color}]{container.get('State', 'N/A')}[/{status_color}]",
                    container.get("Publishers", [{}])[0].get("PublishedPort", "N/A") if container.get("Publishers") else "N/A"
                )
            
            console.print(table)
        else:
            console.print("[yellow]No services running[/yellow]")
            
    except subprocess.CalledProcessError:
        console.print("[yellow]⚠️  No services running or Docker is not available[/yellow]")
    except Exception as e:
        console.print(f"[red]Error checking status: {e}[/red]")


@app.command()
def logs(
    service: Optional[str] = typer.Argument(None, help="Specific service"),
    follow: bool = typer.Option(False, "--follow", "-f", help="Follow logs in real-time"),
    tail: int = typer.Option(100, "--tail", "-n", help="Number of lines")
):
    """📜 Show service logs"""
    compose_file = get_active_compose_file()
    cmd = ["docker", "compose", "-f", compose_file, "logs"]
    
    if follow:
        cmd.append("-f")
    
    cmd.extend(["--tail", str(tail)])
    
    if service:
        cmd.append(service)
    
    try:
        run_command(cmd)
    except KeyboardInterrupt:
        console.print("\n[yellow]Logs interrupted[/yellow]")


@app.command()
def clean(
    volumes: bool = typer.Option(False, "--volumes", "-v", help="Remove volumes too"),
    images: bool = typer.Option(False, "--images", "-i", help="Remove images"),
    all: bool = typer.Option(False, "--all", "-a", help="Remove everything (volumes + images)")
):
    """🧹 Clean containers, volumes and images"""
    
    if all:
        volumes = True
        images = True
    
    console.print("[yellow]🧹 Cleaning Docker environment...[/yellow]\n")
    
    # Stop containers (both compose files)
    console.print("Stopping containers...")
    run_command(["docker", "compose", "-f", "docker-compose-dev.yml", "down"], check=False)
    run_command(["docker", "compose", "-f", "docker-compose.yml", "down"], check=False)
    
    if volumes:
        console.print("Removing volumes...")
        run_command(["docker", "compose", "-f", "docker-compose-dev.yml", "down", "--volumes"], check=False)
        run_command(["docker", "compose", "-f", "docker-compose.yml", "down", "--volumes"], check=False)
    
    if images:
        console.print("Removing images...")
        # Remove project images
        result = subprocess.run(
            ["docker", "images", "-q", "tweet-pulse*"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            image_ids = result.stdout.strip().split('\n')
            run_command(["docker", "rmi", "-f"] + image_ids, check=False)
    
    console.print("\n[green]✓ Cleanup complete![/green]")


@app.command()
def rebuild(
    service: Optional[str] = typer.Argument(None, help="Specific service to rebuild"),
    full: bool = typer.Option(False, "--full", "-f", help="Rebuild full version (with ML). Default: lite")
):
    """🔨 Rebuild Docker images"""
    compose_file = "docker-compose.yml" if full else "docker-compose-dev.yml"
    mode = "FULL" if full else "LITE"
    
    console.print(f"[yellow]🔨 Rebuilding {mode} images...[/yellow]\n")
    
    cmd = ["docker", "compose", "-f", compose_file, "build", "--no-cache"]
    
    if service:
        cmd.append(service)
    
    try:
        run_command(cmd)
        console.print(f"\n[green]✓ Rebuild complete! ({mode} mode)[/green]")
    except subprocess.CalledProcessError:
        console.print("[red]❌ Rebuild error[/red]")
        raise typer.Exit(1)


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    """🌊 Pulse CLI - TweetPulse Control"""
    if ctx.invoked_subcommand is None:
        # If no command passed, open interactive mode
        interactive()


if __name__ == "__main__":
    app()
