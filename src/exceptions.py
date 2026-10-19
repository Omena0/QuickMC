"""Custom exceptions for QuickMC launcher."""


class QuickMCError(Exception):
    """Base exception for QuickMC launcher errors."""


class AuthenticationError(QuickMCError):
    """Raised when authentication fails."""


class ConfigurationError(QuickMCError):
    """Raised when configuration is invalid or missing."""


class InstallationError(QuickMCError):
    """Raised when Minecraft installation fails."""


class LaunchError(QuickMCError):
    """Raised when Minecraft launch fails."""


class JavaNotFoundError(LaunchError):
    """Raised when Java executable cannot be found."""

class WebviewBackendFailException(Exception):
    """Raised when all webview backends raise an exception"""

