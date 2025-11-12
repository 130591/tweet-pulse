#!/usr/bin/env python3
"""
🌊 Pulse CLI - TweetPulse Development Tool
Wrapper script to launch the CLI module
"""

import sys
from pathlib import Path

# Add project root to path if needed
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from cli.src.main import app

if __name__ == "__main__":
    app()
