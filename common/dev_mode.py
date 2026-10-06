"""Process-wide development-mode state."""

_enabled = False


def is_enabled() -> bool:
    return _enabled


def set_enabled(enabled: bool) -> None:
    global _enabled
    _enabled = bool(enabled)
