from dataclasses import dataclass
from pathlib import Path
from typing import Any, Type

from pydantic import BaseModel

from models.subclass import Subclass
from parsers.dispatcher import ABILITY_HANDLER, HANDLERS
from schemas.validator import validate


SCHEMA_ROOT = Path(__file__).resolve().parents[2] / "schemas"


@dataclass(frozen=True)
class EntityDefinition:
    """Validation contract for one supported canonical entity type."""

    entity_type: str
    model: Type[BaseModel]
    schema: str

    def validate_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        model = self.model.model_validate(payload)
        normalized = model.model_dump(mode="json", by_alias=True, exclude_none=True)
        validate(
            SCHEMA_ROOT / "entities" / self.schema,
            normalized,
            SCHEMA_ROOT,
        )
        return normalized


ENTITY_REGISTRY = {
    entity_type: EntityDefinition(entity_type, handler.model, handler.schema)
    for entity_type, handler in {**HANDLERS, "ability": ABILITY_HANDLER}.items()
}
ENTITY_REGISTRY["subclass"] = EntityDefinition(
    "subclass", Subclass, "Subclass.schema.json"
)