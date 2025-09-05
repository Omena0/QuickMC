# Build
py -m nuitka --standalone --windows-console-mode=force \
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

# Copy files
cp -r ../__build/main.dist/* ~/QuickMC/files/

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

echo "QuickMC installed successfully!"
echo "You can now find QuickMC in your applications menu."
echo "QuickMC will launch with console output for better debugging."

