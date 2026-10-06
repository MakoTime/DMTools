from copy import deepcopy
from dataclasses import dataclass

from application.homebrew import HomebrewDraft
from dialog.base.editor import EditorModel


@dataclass
class SpellPropertyEditorModel(HomebrewDraft, EditorModel):
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

    @classmethod
    def from_payload(cls, payload):
        return cls(entity_type="spell", name=payload.get("name", ""), payload=deepcopy(payload))

    def apply(self):
        self.payload["name"] = self.name
        return self
