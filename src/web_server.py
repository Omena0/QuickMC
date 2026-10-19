"""Web server module for handling OAuth callbacks."""

# Re-export from the updated web.py for compatibility
from .web import get_code, reset, start

__all__ = ['get_code', 'reset', 'start']
