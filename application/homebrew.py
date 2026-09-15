from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from application.imports import ENTITY_REGISTRY, ImportedEntityRecord
from components.tree.roots.entity_roots import canonical_entity_type


@dataclass
class HomebrewDraft:
    """Temporary Homebrew editor state discarded unless explicitly applied."""

    entity_type: str
    name: str
    payload: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    draft_state: str = "draft"
    published: bool = False
    version: int = 1
    source_entity_uid: str | None = None
    entity_uid: str | None = field(default=None, repr=False)
    source_identity: str | None = field(default=None, repr=False)

    @classmethod
    def blank(cls, entity_type):
        """Create a valid starting draft for one supported entity type."""
        from application.imports.registry import ENTITY_REGISTRY

        canonical_type = canonical_entity_type(entity_type)
        if canonical_type not in ENTITY_REGISTRY:
            raise ValueError(f"Unsupported Homebrew entity type: {canonical_type}")
        name = f"New {canonical_type.title()}"
        payload = {"name": name}
        required_defaults = {
            "monster": {"challenge_rating": 0},
            "spell": {
                "description": "Add a spell description.",
                "level": 0,
                "casting_time": {"unit": "action"},
                "components": ["V"],
                "duration": {"duration": "instantaneous"},
            },
            "class": {"hit_dice": 1},
            "ability": {"kind": "other", "description": "Add an ability description."},
            "subclass": {"class_name": ""},
        }
        payload.update(required_defaults.get(canonical_type, {}))
        return cls(entity_type=canonical_type, name=name, payload=payload)

    @classmethod
    def from_entity(cls, entity):
        return cls(
            entity_type=entity.entity_type,
            name=entity.name,
            payload=deepcopy(entity.payload),
            source_entity_uid=entity.uid,
        )

    @classmethod
    def for_edit(cls, entity):
        if entity.source_namespace != "homebrew":
            raise ValueError("Only Homebrew entities can be edited")
        metadata = entity.source_metadata
        return cls(
            entity_type=entity.entity_type,
            name=entity.name,
            payload=deepcopy(entity.payload),
            draft_state=metadata.get("draft_state", "draft"),
            published=metadata.get("published", False),
            version=metadata.get("version", 1),
            source_entity_uid=metadata.get("source_entity_uid"),
            entity_uid=entity.uid,
            source_identity=entity.source_identity,
        )

    def validate(self):
        entity_type = canonical_entity_type(self.entity_type)
        payload = deepcopy(self.payload)
        payload["name"] = self.name.strip()
        if not payload["name"]:
            raise ValueError("Homebrew entity name is required")
        normalized = ENTITY_REGISTRY[entity_type].validate_payload(payload)
        if self.version < 1:
            raise ValueError("Homebrew version must be at least 1")
        if self.draft_state not in {"draft", "published", "archived"}:
            raise ValueError(f"Unsupported Homebrew state: {self.draft_state}")
        return entity_type, normalized

    def apply(self):
        entity_type, payload = self.validate()
        entity_uid = self.entity_uid or str(uuid4())
        return ImportedEntityRecord(
            entity_type=entity_type,
            uid=entity_uid,
            source_identity=self.source_identity or f"homebrew:{entity_uid}",
            display_name=payload["name"],
            payload=payload,
            source_metadata={
                "draft_state": self.draft_state,
                "published": self.published,
                "version": self.version,
                "source_entity_uid": self.source_entity_uid,
            },
            provenance="homebrew",
        )