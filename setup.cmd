@echo off

rem QuickMC Standalone Installer for Windows (Batch Script)
rem Usage: Download and run directly, or use the PowerShell one-liner from README.md
rem Prerequisites: Python and Git must be installed

echo QuickMC Standalone Installer
echo ==========================
echo.

rem Check for Git
git --version >nul 2>&1
if errorlevel 1 (
    echo Error: Git is not installed
    echo Install Git from: https://git-scm.com/downloads
    exit /b 1
)

rem Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed
    echo Install Python from: https://python.org/downloads/
    exit /b 1
)

echo Using: 
python --version
git --version

rem Clone repository
echo Cloning QuickMC repository...
if exist "QuickMC" (
    echo QuickMC directory already exists, updating...
    cd QuickMC
    git pull
) else (
    git clone https://github.com/Omena0/QuickMC.git
    cd QuickMC
)

rem Create and activate virtual environment
echo Setting up virtual environment...
python -m venv .venv
call .venv\Scripts\activate.bat

rem Install dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r setup\requirements.txt

rem Build and install
echo Building and installing QuickMC...
cd setup
call install.cmd

echo.
echo Setup Complete! 🚀
echo Find QuickMC in your Start Menu or run: %USERPROFILE%\QuickMC\launch.cmd
