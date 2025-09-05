#!/bin/bash

# QuickMC Launcher
# This script launches the QuickMC binary in a terminal window

cd "$(dirname "$0")"

# Try different terminal emulators in order of preference
launch_in_terminal() {
    local terminals=(
        "gnome-terminal --title='QuickMC' -- bash -c"
        "konsole --title='QuickMC' -e bash -c"
        "xfce4-terminal --title='QuickMC' -e bash -c"
        "xterm -title 'QuickMC' -e bash -c"
        "mate-terminal --title='QuickMC' -e bash -c"
        "terminator --title='QuickMC' -e bash -c"
        "alacritty --title='QuickMC' -e bash -c"
        "kitty --title='QuickMC' bash -c"
    )
    
    local cmd="./files/QuickMC; echo 'Press Enter to close...'; read"
    
    for terminal in "${terminals[@]}"; do
        if command -v ${terminal%% *} >/dev/null 2>&1; then
            echo "Launching QuickMC in ${terminal%% *}..."
            eval "$terminal '$cmd'" &
            exit 0
        fi
    done
    
    # Fallback: run in current terminal
    echo "No GUI terminal found, running in current terminal..."
    ./files/QuickMC
    echo "Press Enter to close..."
    read
}

# Check if running in a terminal or from GUI
if [ -t 0 ]; then
    # Running in terminal already
    echo "QuickMC - Minecraft Launcher"
    echo "============================"
    ./files/QuickMC
    echo ""
    echo "Press Enter to exit..."
    read
else
    # Running from GUI (desktop shortcut, file manager, etc.)
    launch_in_terminal
fi
