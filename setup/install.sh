#!/bin/bash

# QuickMC Installation Script
# This script installs only the necessary runtime files for QuickMC
# It does NOT copy the entire repository - only the compiled executable and required files

# Build
python -m nuitka --standalone --windows-console-mode=force \
 --product-name="QuickMC" --product-version=1.0.0 --file-description="The QuickMC launcher" \
 --copyright="Copyright © 2025 Omena0. All rights reserved." \
 --output-dir="../__build" \
 --include-package-data="minecraft_launcher_lib" \
 --deployment --python-flag="-OO" --python-flag="-S" \
 --assume-yes-for-downloads \
 --lto=yes \
 --jobs=16 \
 --output-filename="QuickMC" \
 ../src/main.py

# Make directories
mkdir -p ~/QuickMC/files
mkdir -p ~/QuickMC/data
mkdir -p ~/QuickMC/.minecraft

# Copy runtime files (compiled executable and dependencies only)
cp -r ../__build/main.dist/* ~/QuickMC/files/

# Clean up any development files that might have been included
rm -f ~/QuickMC/files/*.py 2>/dev/null || true
rm -f ~/QuickMC/files/*.pyc 2>/dev/null || true
rm -rf ~/QuickMC/files/__pycache__ 2>/dev/null || true
rm -rf ~/QuickMC/files/.git* 2>/dev/null || true

# Copy config
cp ../config.json ~/QuickMC/data/

# Copy console launcher
cp launch.sh ~/QuickMC/
chmod +x ~/QuickMC/launch.sh

# Create a application launcher shortcut
mkdir -p ~/.local/share/applications/

# Copy the desktop file and modify the paths
cp QuickMC.desktop ~/.local/share/applications/quickmc.desktop
sed -i "s|/home/%USER%|$HOME|g" ~/.local/share/applications/quickmc.desktop

chmod +x ~/.local/share/applications/quickmc.desktop

echo "Done!"
