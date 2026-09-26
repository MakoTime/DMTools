"""Pytest-wide environment setup for GUI tests."""

import os


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
