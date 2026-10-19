#!/usr/bin/env python3
"""
QuickMC - A simplified Minecraft launcher

This is the main entry point for the QuickMC launcher application.
"""

from app import QuickMCApp

# Configuration constants
DEBUG_OAUTH = False


def main():
    """Main entry point for QuickMC launcher."""
    # Create and run the application
    app = QuickMCApp(debug_oauth=DEBUG_OAUTH)
    app.run()


if __name__ == '__main__':
    main()

