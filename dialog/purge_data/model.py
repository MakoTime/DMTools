from dataclasses import dataclass, field

from components.tree.roots.entity_roots import ENTITY_CATEGORIES


ENTITY_TYPES = tuple(entity_type for entity_type, _label in ENTITY_CATEGORIES)


@dataclass
class PurgeDataModel:
    namespace: str = "compendium"
    entity_types: set[str] = field(default_factory=lambda: set(ENTITY_TYPES))

    def set_namespace(self, namespace):
        if namespace not in {"compendium", "homebrew"}:
            raise ValueError(f"Unsupported entity namespace: {namespace}")
        self.namespace = namespace

    def set_entity_types(self, entity_types):
        selected = set(entity_types)
        invalid = selected.difference(ENTITY_TYPES)
        if invalid:
            raise ValueError(f"Unsupported entity types: {sorted(invalid)}")
        self.entity_types = selected

    def validate(self):
        if not self.entity_types:
            raise ValueError("Select at least one entity type to purge")