#!/bin/bash

# QuickMC Fast Launcher - Optimized for speed

cd "$(dirname "$0")"

# Quick executable check
[ ! -f "./files/QuickMC" ] && { echo "Error: QuickMC not found"; exit 1; }

# Ultra-fast terminal launch based on desktop environment
case "${XDG_CURRENT_DESKTOP:-}" in
    "KDE")
        exec konsole --title 'QuickMC' -e "./files/QuickMC" >/dev/null 2>&1 &
        ;;
    "GNOME"|"ubuntu:GNOME")
        if command -v gnome-terminal >/dev/null; then
            exec gnome-terminal --title='QuickMC' -- "./files/QuickMC" >/dev/null 2>&1 &
        elif command -v alacritty >/dev/null; then
            exec alacritty --title 'QuickMC' -e "./files/QuickMC" >/dev/null 2>&1 &
        fi
        ;;
    *)
        # Fast fallback detection
        for term in konsole alacritty kitty xterm; do
            if command -v "$term" >/dev/null 2>&1; then
                case $term in
                    konsole) 
                        exec konsole --title 'QuickMC' -e "./files/QuickMC" >/dev/null 2>&1 &
                        ;;
                    alacritty) 
                        exec alacritty --title 'QuickMC' -e "./files/QuickMC" >/dev/null 2>&1 &
                        ;;
                    kitty) 
                        exec kitty --title='QuickMC' "./files/QuickMC" >/dev/null 2>&1 &
                        ;;
                    xterm) 
                        exec xterm -title 'QuickMC' -e "./files/QuickMC" >/dev/null 2>&1 &
                        ;;
                esac
                break
            fi
        done
        # If no terminal found, run directly
        exec ./files/QuickMC
        ;;
esac
