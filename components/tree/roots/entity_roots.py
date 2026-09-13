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

    def category(self, entity_type: str) -> EntityCategoryNode:
        return self.categories[category_entity_type(entity_type)]


compendium_root = EntityRootNode("compendium", "Compendium")
homebrew_root = EntityRootNode("homebrew", "Homebrew")