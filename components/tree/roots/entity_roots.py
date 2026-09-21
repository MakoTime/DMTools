import json
from pathlib import Path

from common.icons import get_icon
from components.tree.model import TreeNode


ENTITY_CATEGORIES = (
    ("item", "Item"),
    ("spell", "Spells"),
    ("race", "Races"),
    ("class", "Classes"),
    ("subclass", "Subclasses"),
    ("monster", "Monsters"),
    ("feat", "Feats"),
    ("background", "Backgrounds"),
    ("ability", "Abilities"),
)

ENTITY_TYPE_CATEGORIES = {
    **{entity_type: entity_type for entity_type, _label in ENTITY_CATEGORIES},
}

_CANONICAL_ENTITY_TYPES = {
    label.lower(): entity_type
    for entity_type, label in ENTITY_CATEGORIES
}
_CANONICAL_ENTITY_TYPES.update(
    {entity_type: entity_type for entity_type in ENTITY_TYPE_CATEGORIES}
)


def canonical_entity_type(value: str) -> str:
    """Return the stable entity type represented by a type or display label."""
    try:
        return _CANONICAL_ENTITY_TYPES[value.strip().lower()]
    except (AttributeError, KeyError) as error:
        raise ValueError(f"Unsupported entity type: {value}") from error


def category_entity_type(value: str) -> str:
    """Return the category type that owns one canonical entity type."""
    return ENTITY_TYPE_CATEGORIES[canonical_entity_type(value)]


class EntityCategoryNode(TreeNode):
    """Protected destination for one canonical entity type."""

    node_type = "entity_category"
    protected = True

    def __init__(self, namespace: str, entity_type: str, display_name: str):
        super().__init__(
            display_name,
            icon=get_icon("folder"),
            uid=f"dmtools-{namespace}-{entity_type}-category",
        )
        self.namespace = namespace
        self.entity_type = entity_type

    def validate_entity_type(self, entity_type: str) -> str:
        canonical_type = canonical_entity_type(entity_type)
        if category_entity_type(canonical_type) != self.entity_type:
            raise ValueError(
                f"Cannot add {canonical_type} to {self.name}; "
                f"expected {self.entity_type}"
            )
        return canonical_type

    def add_entity_node(self, child_node: TreeNode, entity_type: str) -> TreeNode:
        self.validate_entity_type(entity_type)
        self.add_child(child_node)
        return child_node


class RulesCategoryNode(TreeNode):
    """Protected destination for one compendium rules category."""

    node_type = "rules_category"
    protected = True

    def __init__(
        self,
        namespace: str,
        category_type: str,
        display_name: str,
        schema_names=(),
    ):
        super().__init__(
            display_name,
            icon=get_icon("folder"),
            uid=f"dmtools-{namespace}-rules-{category_type}",
        )
        self.namespace = namespace
        self.category_type = category_type
        self.schema_names = tuple(schema_names)

    def populate_values(self):
        self.children.clear()
        self.child_uids.clear()
        for value in _schema_enum_values(self.schema_names):
            self.add_child(
                RulesValueNode(
                    self.namespace,
                    self.category_type,
                    value,
                    self.schema_names,
                )
            )


class RulesSubcategoryNode(TreeNode):
    """Protected destination for one subdivision of a rules category."""

    node_type = "rules_subcategory"
    protected = True

    def __init__(
        self,
        namespace: str,
        parent_type: str,
        category_type: str,
        display_name: str,
        schema_names=(),
    ):
        super().__init__(
            display_name,
            icon=get_icon("folder"),
            uid=f"dmtools-{namespace}-rules-{parent_type}-{category_type}",
        )
        self.namespace = namespace
        self.parent_type = parent_type
        self.category_type = category_type
        self.schema_names = tuple(schema_names)

    def populate_values(self):
        self.children.clear()
        self.child_uids.clear()
        for value in _schema_enum_values(self.schema_names):
            self.add_child(
                RulesValueNode(
                    self.namespace,
                    f"{self.parent_type}-{self.category_type}",
                    value,
                    self.schema_names,
                )
            )


class RulesValueNode(TreeNode):
    """Protected canonical value exposed by a Rules category."""

    node_type = "rules_value"
    protected = True

    def __init__(self, namespace: str, category_type: str, value: str, schema_names):
        super().__init__(
            value.replace("_", " ").title(),
            icon=get_icon("folder"),
            uid=f"dmtools-{namespace}-rules-{category_type}-{value}",
        )
        self.namespace = namespace
        self.category_type = category_type
        self.value = value
        self.schema_names = tuple(schema_names)


_SCHEMA_ROOT = Path(__file__).resolve().parents[3] / "schemas"


def _schema_enum_values(schema_names):
    values = []

    def collect_enums(value):
        if isinstance(value, dict):
            for enum_value in value.get("enum", ()):
                if enum_value not in values and isinstance(enum_value, (str, int)):
                    values.append(enum_value)
            for child in value.values():
                collect_enums(child)
        elif isinstance(value, list):
            for child in value:
                collect_enums(child)

    for schema_name in schema_names:
        relative_path = schema_name
        if "/" not in relative_path:
            relative_path = f"values/{relative_path}"
        path = _SCHEMA_ROOT / f"{relative_path}.schema.json"
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            continue
        collect_enums(schema)
    return tuple(values)


def _load_schema(schema_path):
    try:
        return json.loads(schema_path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def _resolve_schema_ref(reference, current_path):
    if not reference or reference.startswith("#"):
        return None
    return (current_path.parent / reference).resolve()


def custom_rule_values(entity_type, payload):
    """Return custom schema values found in one validated homebrew entity."""
    entity_path = _SCHEMA_ROOT / "entities" / f"{entity_type.title()}.schema.json"
    values = []

    def visit(schema, value, current_path):
        if not isinstance(schema, dict):
            return
        reference = schema.get("$ref")
        if reference:
            referenced_path = _resolve_schema_ref(reference, current_path)
            if referenced_path is None:
                return
            if referenced_path.parent.name == "values" and isinstance(value, str):
                referenced_schema = _load_schema(referenced_path)
                if referenced_schema is None:
                    return
                schema_name = referenced_path.stem.removesuffix(".schema")
                if value not in _schema_enum_values((schema_name,)):
                    values.append((schema_name, value))
                return
            referenced_schema = _load_schema(referenced_path)
            if referenced_schema is not None:
                visit(referenced_schema, value, referenced_path)
            return
        for alternative in schema.get("oneOf", schema.get("anyOf", ())):
            visit(alternative, value, current_path)
        if isinstance(value, dict):
            for name, child in value.items():
                visit(schema.get("properties", {}).get(name), child, current_path)
        elif isinstance(value, list):
            for child in value:
                visit(schema.get("items"), child, current_path)

    schema = _load_schema(entity_path)
    if schema is not None:
        visit(schema, payload, entity_path)
    return tuple(dict.fromkeys(values))


class RulesRootNode(TreeNode):
    """Protected sub-root for shared compendium rules references."""

    node_type = "rules_root"
    protected = True

    CATEGORIES = (
        ("proficiencies", "Proficiencies", ()),
        ("weapons", "Weapons", ()),
        ("ability_score", "Ability Scores", ("ability_score",)),
        (
            "ability_kind",
            "Ability Kinds",
            ("entities/Ability",),
        ),
        ("alignment", "Alignments", ("alignment",)),
        ("action_type", "Action Types", ("action_type",)),
        ("attack_type", "Attack Types", ("attack_type",)),
        ("bonus_type", "Bonus Types", ("components/bonus",)),
        ("casting_time", "Casting Time Units", ("components/casting_time",)),
        ("class_name", "Class Names", ("class_name",)),
        ("conditions", "Conditions", ("condition",)),
        ("distance_type", "Distance Units", ("distance_type",)),
        ("duration", "Duration Units", ("duration",)),
        ("movement_type", "Movement Types", ("movement_type",)),
        ("recharge", "Recharge Times", ("recharge",)),
        ("size", "Sizes", ("size",)),
        ("sense", "Senses", ("sense_type",)),
        ("spell_component", "Spell Components", ("spell_component",)),
        ("spell_school", "Spell Schools", ("spell_school",)),
        ("currency", "Currencies", ("currency",)),
        ("rarity", "Rarities", ("rarity",)),
        ("creature_type", "Creature Types", ("creature_type",)),
        ("damage_type", "Damage Types", ("damage_type",)),
        (
            "spellcasting_progression",
            "Spellcasting Progressions",
            ("spellcasting_progression",),
        ),
        ("item_category", "Item Categories", ("item_category",)),
        ("target_type", "Target Types", ("target_type",)),
        ("target_zone", "Target Zones", ("target_zone",)),
        ("targeting", "Targeting Modes", ("components/target",)),
    )
    PROFICIENCY_CATEGORIES = (
        ("languages", "Languages", ("language",)),
        ("skills", "Skills", ("skill",)),
        ("tools", "Tools", ("tool",)),
        (
            "armor",
            "Armor",
            ("armor_category", "armor_type", "armor_proficiency"),
        ),
        ("instruments", "Instruments", ("instrument",)),
        ("gaming_sets", "Gaming Sets", ("gaming_set",)),
        ("vehicles", "Vehicles", ("vehicle",)),
    )

    def __init__(self, namespace: str, *, canonical_values=True):
        super().__init__(
            "Rules",
            icon=get_icon("folder"),
            uid=f"dmtools-{namespace}-rules-root",
        )
        self.namespace = namespace
        self.canonical_values = canonical_values
        self.categories = {
            category_type: RulesCategoryNode(
                namespace, category_type, label, schema_names
            )
            for category_type, label, schema_names in self.CATEGORIES
        }
        proficiencies = self.categories["proficiencies"]
        for category_type, label, schema_names in self.PROFICIENCY_CATEGORIES:
            proficiencies.add_child(
                RulesSubcategoryNode(
                    namespace,
                    "proficiencies",
                    category_type,
                    label,
                    schema_names,
                )
            )
        self.reset()

    def reset(self):
        self.children.clear()
        self.child_uids.clear()
        for category in self.categories.values():
            category.children.clear()
            category.child_uids.clear()
            category.parent = None
            category.parent_uid = None
            self.add_child(category)
            if self.canonical_values:
                category.populate_values()
        weapons = self.categories["weapons"]
        for category_type, label, schema_names in (
            ("groups", "Groups", ("weapon_category",)),
            ("types", "Types", ("weapon_type",)),
            ("tags", "Tags", ("weapon_property",)),
        ):
            weapons.add_child(
                RulesSubcategoryNode(
                    self.namespace,
                    "weapons",
                    category_type,
                    label,
                    schema_names,
                )
            )
        proficiencies = self.categories["proficiencies"]
        for category_type, label, schema_names in self.PROFICIENCY_CATEGORIES:
            proficiencies.add_child(
                RulesSubcategoryNode(
                    self.namespace,
                    "proficiencies",
                    category_type,
                    label,
                    schema_names,
                )
            )
        for category in proficiencies.children:
            if self.canonical_values:
                category.populate_values()
        for category in weapons.children:
            if self.canonical_values:
                category.populate_values()

    def set_custom_values(self, values):
        """Replace Homebrew Rules values with validated custom schema values."""
        self.reset()
        for schema_name, value in values:
            target = None
            for category in self.categories.values():
                if schema_name in category.schema_names:
                    target = category
                    break
                for subcategory in category.children:
                    if schema_name in subcategory.schema_names:
                        target = subcategory
                        break
                if target is not None:
                    break
            if target is None:
                continue
            if any(child.value == value for child in target.children):
                continue
            target.add_child(
                RulesValueNode(
                    self.namespace,
                    target.category_type,
                    value,
                    target.schema_names,
                )
            )

    def category(self, category_type: str) -> RulesCategoryNode:
        return self.categories[category_type.strip().lower()]


class EntityRootNode(TreeNode):
    """Persistent root containing the ordered entity categories for a namespace."""

    node_type = "entity_root"
    protected = True

    def __init__(self, namespace: str, display_name: str):
        super().__init__(
            display_name,
            icon=get_icon("folder"),
            uid=f"dmtools-{namespace}-root",
        )
        self.namespace = namespace
        self.categories = {
            entity_type: EntityCategoryNode(namespace, entity_type, label)
            for entity_type, label in ENTITY_CATEGORIES
        }
        self.rules = RulesRootNode(
            namespace,
            canonical_values=namespace == "compendium",
        )
        self.reset()

    def reset(self):
        self.children.clear()
        self.child_uids.clear()
        for category in self.categories.values():
            category.children.clear()
            category.child_uids.clear()
            category.parent = None
            category.parent_uid = None
            self.add_child(category)
        if self.rules is not None:
            self.rules.reset()
            self.add_child(self.rules)

    def category(self, entity_type: str) -> EntityCategoryNode:
        return self.categories[category_entity_type(entity_type)]


compendium_root = EntityRootNode("compendium", "Compendium")
homebrew_root = EntityRootNode("homebrew", "Homebrew")