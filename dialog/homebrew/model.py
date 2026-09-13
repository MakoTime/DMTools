from copy import deepcopy
from dataclasses import dataclass

from application.homebrew import HomebrewDraft
from application.imports import ENTITY_REGISTRY
from components.tree.roots.entity_roots import canonical_entity_type
from dialog.base.editor import EditorModel


@dataclass
class HomebrewEditorModel(HomebrewDraft, EditorModel):
    """Temporary adaptive editor state validated by the entity registry."""

    @classmethod
    def from_draft(cls, draft):
        return cls(
            entity_type=draft.entity_type,
            name=draft.name,
            payload=deepcopy(draft.payload),
            description=draft.description,
            draft_state=draft.draft_state,
            published=draft.published,
            version=draft.version,
            source_entity_uid=draft.source_entity_uid,
            entity_uid=draft.entity_uid,
            source_identity=draft.source_identity,
        )


def create_homebrew_editor_model(entity_type, draft=None):
    entity_type = canonical_entity_type(entity_type)
    if entity_type not in ENTITY_REGISTRY:
        raise ValueError(f"Unsupported Homebrew entity type: {entity_type}")
    if draft is not None:
        model = HomebrewEditorModel.from_draft(draft)
        if canonical_entity_type(model.entity_type) != entity_type:
            raise ValueError("Homebrew draft type does not match the requested editor")
        return model
    return HomebrewEditorModel(entity_type=entity_type, name="", payload={})