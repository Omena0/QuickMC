"""Web server module for handling OAuth callbacks."""

# Re-export from the updated web.py for compatibility
from .web import start, get_code, reset

__all__ = ['start', 'get_code', 'reset']
