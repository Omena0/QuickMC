"""Custom exceptions for QuickMC launcher."""


class QuickMCError(Exception):
    """Base exception for QuickMC launcher errors."""
    pass


class AuthenticationError(QuickMCError):
    """Raised when authentication fails."""
    pass


class ConfigurationError(QuickMCError):
    """Raised when configuration is invalid or missing."""
    pass


class InstallationError(QuickMCError):
    """Raised when Minecraft installation fails."""
    pass


class LaunchError(QuickMCError):
    """Raised when Minecraft launch fails."""
    pass


class JavaNotFoundError(LaunchError):
    """Raised when Java executable cannot be found."""
    pass
