#!/bin/bash
# Pulse CLI installation script

set -e

echo "🌊 Installing Pulse CLI..."
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r cli/requirements.txt

# Make executable
echo "🔧 Setting permissions..."
chmod +x pulse.py

# Create alias
SHELL_RC=""
if [ -f "$HOME/.bashrc" ]; then
    SHELL_RC="$HOME/.bashrc"
elif [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

if [ -n "$SHELL_RC" ]; then
    ALIAS_LINE="alias pulse='python3 $(pwd)/pulse.py'"
    
    # Check if alias already exists
    if grep -q "alias pulse=" "$SHELL_RC"; then
        echo "⚠️  Alias 'pulse' already exists in $SHELL_RC"
    else
        echo ""
        echo "Would you like to add the 'pulse' alias to your shell? ($SHELL_RC)"
        echo "This will allow you to use just 'pulse' instead of 'python3 pulse.py'"
        read -p "Add alias? (y/n) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "" >> "$SHELL_RC"
            echo "# Pulse CLI - TweetPulse" >> "$SHELL_RC"
            echo "$ALIAS_LINE" >> "$SHELL_RC"
            echo "✅ Alias added to $SHELL_RC"
            echo "Run: source $SHELL_RC"
            echo "Or open a new terminal"
        fi
    fi
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "🚀 How to use:"
echo "  python3 pulse.py              # Interactive mode"
echo "  python3 pulse.py dev all      # Run everything"
echo "  python3 pulse.py --help       # See all commands"
echo ""

if [ -n "$SHELL_RC" ] && grep -q "alias pulse=" "$SHELL_RC"; then
    echo "💡 After loading the alias, you can simply use:"
    echo "  pulse                # Interactive mode"
    echo "  pulse dev frontend   # Run frontend"
    echo "  pulse status         # Check status"
    echo ""
fi

echo "📖 See CLI_README.md for more information"
