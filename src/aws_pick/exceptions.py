"""Custom exceptions for aws-pick."""


class InvalidAccountError(ValueError):
    """Raised when an account dict is missing required fields or has invalid values."""


class InvalidSelectionError(ValueError):
    """Raised when a non-interactive selection references an account/role not in the input list."""


class ConfigCorruptedError(Exception):
    """Raised when a configuration file is corrupted and cannot be parsed."""


class PresetNotFoundError(KeyError):
    """Raised when a requested preset does not exist."""
