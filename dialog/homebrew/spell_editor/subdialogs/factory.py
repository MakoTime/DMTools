from PySide6.QtWidgets import QWidget

from .model import (
    CastingTimeModel,
    DurationModel,
    EffectModel,
    EffectsModel,
    GrantModel,
    GrantsModel,
    MaterialModel,
    RollTableEntryModel,
    RollTableModel,
    TargetModel,
)
from .view import (
    CastingTimeDialog,
    DurationDialog,
    EffectDialog,
    EffectsDialog,
    GrantDialog,
    GrantsDialog,
    MaterialDialog,
    RollTableDialog,
    RollTableEntryDialog,
    TargetDialog,
)


def create_casting_time_dialog(value=None, parent: QWidget | None = None):
    return CastingTimeDialog(value, parent=parent, editor_model=CastingTimeModel(value))


def create_duration_dialog(value=None, parent: QWidget | None = None):
    return DurationDialog(value, parent=parent, editor_model=DurationModel(value or {}))


def create_material_dialog(value=None, parent: QWidget | None = None):
    return MaterialDialog(value, parent=parent, editor_model=MaterialModel(value or {}))


def create_target_dialog(value=None, parent: QWidget | None = None):
    return TargetDialog(value, parent=parent, editor_model=TargetModel(value or {}))


def create_effect_dialog(value=None, parent: QWidget | None = None):
    return EffectDialog(value, parent=parent, editor_model=EffectModel(value))


def create_effects_dialog(values=None, parent: QWidget | None = None):
    return EffectsDialog(values, parent=parent, editor_model=EffectsModel(values or []))


def create_grant_dialog(value=None, parent: QWidget | None = None):
    return GrantDialog(value, parent=parent, editor_model=GrantModel(value or {}))


def create_grants_dialog(values=None, parent: QWidget | None = None):
    return GrantsDialog(values, parent=parent, editor_model=GrantsModel(values or []))


def create_roll_table_dialog(value=None, parent: QWidget | None = None):
    return RollTableDialog(value, parent=parent, editor_model=RollTableModel(value or {}))


def create_roll_table_entry_dialog(value=None, parent: QWidget | None = None):
    return RollTableEntryDialog(
        value,
        parent=parent,
        editor_model=RollTableEntryModel(value or {}),
    )
