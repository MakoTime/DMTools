"""Project metadata versioning and upgrade steps.

Keep schema migrations here so loading an older project does not spread
version checks throughout the persistence code.
"""

from collections.abc import Callable
from typing import Any


CURRENT_PROJECT_VERSION = 1
VERSION_KEY = "version"

UpgradeStep = Callable[[dict[str, Any]], dict[str, Any]]


UPGRADE_STEPS: dict[int, UpgradeStep] = {}


def upgrade_project_data(data: dict[str, Any]) -> dict[str, Any]:
    """Upgrade project metadata to ``CURRENT_PROJECT_VERSION``."""
    version = data.get(VERSION_KEY)
    if not isinstance(version, int):
        raise ValueError("Project metadata has no valid version")
    if version > CURRENT_PROJECT_VERSION:
        raise ValueError(
            f"Project version {version} is newer than supported version "
            f"{CURRENT_PROJECT_VERSION}"
        )

    upgraded = dict(data)
    while version < CURRENT_PROJECT_VERSION:
        try:
            upgrade = UPGRADE_STEPS[version]
        except KeyError as error:
            raise ValueError(
                f"No upgrade path from project version {version}"
            ) from error
        upgraded = upgrade(upgraded)
        version = upgraded[VERSION_KEY]
    return upgraded
