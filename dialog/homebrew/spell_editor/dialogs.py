"""Backward-compatible imports for Spell child editor views.

New code should construct these views through ``subdialogs.factory``.
"""

from .subdialogs.view import (
    CastingTimeDialog,
    DurationDialog,
    EffectDialog,
    EffectsDialog,
    GrantDialog,
    GrantsDialog,
    MaterialDialog,
    RollTableDialog,
    RollTableEntryDialog,
    SpellChildDialog,
    TargetDialog,
)

__all__ = [
    "CastingTimeDialog",
    "DurationDialog",
    "EffectDialog",
    "EffectsDialog",
    "GrantDialog",
    "GrantsDialog",
    "MaterialDialog",
    "RollTableDialog",
    "RollTableEntryDialog",
    "SpellChildDialog",
    "TargetDialog",
]
