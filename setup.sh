#!/bin/bash

# QuickMC One-Line Installer
# Usage: curl -sSL https://raw.githubusercontent.com/Omena0/QuickMC/master/setup.sh | bash
# Prerequisites: Python and Git must be installed

set -e

echo "QuickMC One-Line Installer"
echo "=========================="
echo ""

# Check for Git
if ! command -v git >/dev/null 2>&1; then
    echo "Error: Git is not installed"
    echo "Install git first, then run this script"
    exit 1
fi

# Check for Python
PYTHON_CMD="python3"
if ! command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="python"
fi

if ! command -v $PYTHON_CMD >/dev/null 2>&1; then
    echo "Error: Python is not installed"
    exit 1
fi

echo "Using: $($PYTHON_CMD --version)"
echo "Using: $(git --version)"

# Clone repository
echo "Cloning QuickMC repository..."
if [ -d "QuickMC" ]; then
    echo "QuickMC directory already exists, updating..."
    cd QuickMC
    git pull
else
    git clone https://github.com/Omena0/QuickMC.git
    cd QuickMC
fi

# Create and activate virtual environment
echo "Setting up virtual environment..."
$PYTHON_CMD -m venv .venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
python -m pip install --upgrade pip
if command -v uv >/dev/null 2>&1; then
    uv pip install -r setup/requirements.txt
else
    pip install -r setup/requirements.txt
fi

# Build and install
echo "Building and installing QuickMC..."
cd setup && bash install.sh

echo ""
echo "Setup Complete! 🚀"
echo "Find QuickMC in your applications menu or run: ~/QuickMC/launch.sh"
