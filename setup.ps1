# QuickMC One-Line Installer for Windows (PowerShell)
# Usage: iwr -useb https://raw.githubusercontent.com/Omena0/QuickMC/master/setup.ps1 | iex
# Prerequisites: Python and Git must be installed

Write-Host "QuickMC One-Line Installer" -ForegroundColor Cyan
Write-Host "==========================" -ForegroundColor Cyan
Write-Host ""

# Check for Git
try {
    $gitVersion = git --version 2>$null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "✓ Git: $gitVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: Git is not installed" -ForegroundColor Red
    Write-Host "  Install Git from: https://git-scm.com/downloads" -ForegroundColor Yellow
    exit 1
}

# Check for Python
try {
    $pythonVersion = python --version 2>$null
    if ($LASTEXITCODE -ne 0) { throw }
    Write-Host "✓ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Error: Python is not installed" -ForegroundColor Red
    Write-Host "  Install Python from: https://python.org/downloads/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Clone or update repository
if (Test-Path "QuickMC") {
    Write-Host "QuickMC directory already exists, updating..." -ForegroundColor Yellow
    Set-Location QuickMC
    git pull
} else {
    Write-Host "Cloning QuickMC repository..." -ForegroundColor Cyan
    git clone https://github.com/Omena0/QuickMC.git
    Set-Location QuickMC
}

# Create and activate virtual environment
Write-Host "Setting up virtual environment..." -ForegroundColor Cyan
python -m venv .venv
& .\.venv\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
python -m pip install --upgrade pip | Out-Null
pip install -r setup\requirements.txt

# Build and install
Write-Host "Building and installing QuickMC..." -ForegroundColor Cyan
Set-Location setup
& .\install.cmd

Write-Host ""
Write-Host "Setup Complete! 🚀" -ForegroundColor Green
Write-Host "Find QuickMC in your Start Menu or run: $env:USERPROFILE\QuickMC\launch.cmd" -ForegroundColor Cyan
