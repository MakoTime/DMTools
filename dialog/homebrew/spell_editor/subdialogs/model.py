from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from dialog.base.editor import EditorModel


@dataclass
class SpellChildModel(EditorModel):
    """Draft state shared by a modeless Spell child editor."""

    value: Any = None

    def __post_init__(self):
        self.value = deepcopy(self.value)

    def apply(self):
        self.validate()
        return deepcopy(self.value)


@dataclass
class CastingTimeModel(SpellChildModel):
    pass


@dataclass
class DurationModel(SpellChildModel):
    pass


@dataclass
class MaterialModel(SpellChildModel):
    pass


@dataclass
class TargetModel(SpellChildModel):
    pass


@dataclass
class GrantModel(SpellChildModel):
    pass


@dataclass
class GrantsModel(SpellChildModel):
    pass


@dataclass
class EffectModel(SpellChildModel):
    pass


@dataclass
class EffectsModel(SpellChildModel):
    pass


@dataclass
class RollTableModel(SpellChildModel):
    pass


@dataclass
class RollTableEntryModel(SpellChildModel):
    pass
