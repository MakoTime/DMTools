from PySide6.QtWidgets import QTableWidget


class HomebrewPropertyTable(QTableWidget):
    """Base table for the explicitly designed fields of one entity type."""

    property_names = ()


class AbilityPropertyTable(HomebrewPropertyTable):
    property_names = (
        "kind", "description", "level", "classes", "prerequisites", "source",
    )


class BackgroundPropertyTable(HomebrewPropertyTable):
    property_names = (
        "description", "skill_proficiencies", "tool_proficiencies", "languages",
        "features", "equipment", "tags", "source",
    )


class ClassPropertyTable(HomebrewPropertyTable):
    property_names = (
        "description", "hit_dice", "primary_abilities", "saving_throws",
        "armor_proficiencies", "weapon_proficiencies", "tool_proficiencies",
        "skill_choices", "features", "repeating_features", "required_stats",
        "starting_class", "multiclassing", "ability_score_increase",
        "spellcasting", "subclass_level", "tags", "source",
    )


class CreaturePropertyTable(HomebrewPropertyTable):
    property_names = (
        "description", "size", "creature_type", "alignment", "ability_scores",
        "hit_points", "hit_dice", "armor_class", "movement", "saving_throws",
        "skills", "senses", "passive_perception", "languages",
        "proficiency_bonus", "condition_immunities", "damage_immunities",
        "damage_resistances", "damage_vulnerabilities", "features", "actions",
        "reactions", "legendary_actions", "spell_casting", "roll_table",
        "challenge_rating", "environments", "image", "source",
    )


class FeatPropertyTable(HomebrewPropertyTable):
    property_names = (
        "description", "prerequisite", "ability_score_increases",
        "skill_proficiencies", "tool_proficiencies", "vehicle_proficiencies",
        "instrument_proficiencies", "gaming_set_proficiencies",
        "weapon_proficiencies", "armor_proficiencies", "spell_grants",
        "actions", "tags", "features", "source",
    )


class ItemPropertyTable(HomebrewPropertyTable):
    property_names = (
        "description", "category", "weapon", "armor", "magic_item", "weight",
        "cost", "features", "source", "image",
    )


class RacePropertyTable(HomebrewPropertyTable):
    property_names = (
        "subtype", "size", "movement", "ability_score_increases", "features",
        "actions", "skill_proficiencies", "weapon_proficiencies",
        "armor_proficiencies", "tool_proficiencies", "vehicle_proficiencies",
        "instrument_proficiencies", "gaming_set_proficiencies", "languages",
        "spell_grants", "feats", "senses", "source",
    )


class SpellPropertyTable(HomebrewPropertyTable):
    property_names = (
        "description", "higher_level", "level", "school", "classes",
        "casting_time", "target", "components", "material", "ritual",
        "concentration", "duration", "effects", "roll_table", "tags",
        "source", "grants",
    )


class SubclassPropertyTable(HomebrewPropertyTable):
    property_names = (
        "class", "description", "features", "spells", "tags", "source",
    )


PROPERTY_TABLES = {
    "ability": AbilityPropertyTable,
    "background": BackgroundPropertyTable,
    "class": ClassPropertyTable,
    "monster": CreaturePropertyTable,
    "feat": FeatPropertyTable,
    "item": ItemPropertyTable,
    "race": RacePropertyTable,
    "spell": SpellPropertyTable,
    "subclass": SubclassPropertyTable,
}
