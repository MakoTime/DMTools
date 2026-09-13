from dataclasses import asdict, dataclass, replace
import re
from typing import Literal


EntityNamespace = Literal["compendium", "homebrew", "collection"]


@dataclass(frozen=True)
class EntityReference:
    target_uid: str
    entity_type: str
    source_namespace: EntityNamespace
    display_fallback: str | None = None


@dataclass(frozen=True)
class ReferenceDiagnostic:
    path: str
    entity_type: str
    display_fallback: str
    status: Literal["missing", "ambiguous"]
    candidate_uids: tuple[str, ...] = ()


def normalize_entity_references(
    records, existing_entities=(), *, source_namespace="compendium"
):
    """Attach UID references for known structured links without changing payloads."""
    records = tuple(records)
    index = {}
    for entity in (*tuple(existing_entities), *records):
        key = (entity.entity_type, _entity_name(entity).casefold())
        index.setdefault(key, {})[entity.uid] = entity
    spell_names = {
        _entity_name(entity): entity
        for entity in (*tuple(existing_entities), *records)
        if entity.entity_type == "spell" and _entity_name(entity)
    }
    normalized = []
    for record in records:
        references = []
        diagnostics = []
        candidates = list(extract_reference_candidates(record.entity_type, record.payload))
        if record.entity_type != "spell":
            candidates.extend(_extract_text_spell_candidates(record.payload, spell_names))
        seen_candidates = set()
        for path, entity_type, name in candidates:
            lookup_name = (
                _normalize_spell_reference_name(name)
                if entity_type == "spell"
                else name
            )
            candidate_key = (entity_type, lookup_name.casefold())
            if candidate_key in seen_candidates:
                continue
            seen_candidates.add(candidate_key)
            candidates = tuple(index.get((entity_type, lookup_name.casefold()), {}).values())
            if len(candidates) == 1:
                target = candidates[0]
                namespace = getattr(target, "source_namespace", source_namespace)
                references.append(
                    {
                        "path": path,
                        **asdict(
                            EntityReference(
                                target_uid=target.uid,
                                entity_type=entity_type,
                                source_namespace=namespace,
                                display_fallback=lookup_name,
                            )
                        ),
                    }
                )
            else:
                diagnostics.append(
                    asdict(
                        ReferenceDiagnostic(
                            path=path,
                            entity_type=entity_type,
                            display_fallback=lookup_name,
                            status="ambiguous" if candidates else "missing",
                            candidate_uids=tuple(item.uid for item in candidates),
                        )
                    )
                )
        metadata = dict(record.source_metadata)
        metadata.pop("entity_references", None)
        metadata.pop("reference_diagnostics", None)
        if references:
            metadata["entity_references"] = references
        if diagnostics:
            metadata["reference_diagnostics"] = diagnostics
        normalized.append(replace(record, source_metadata=metadata))
    return tuple(normalized)


def _normalize_spell_reference_name(name: str) -> str:
    return re.sub(r"^(?:and|or)\s+", "", name.strip(), flags=re.IGNORECASE)


def _extract_text_spell_candidates(payload, spell_names):
    candidates = []
    for path, text in _text_values(payload):
        for name in sorted(spell_names, key=len, reverse=True):
            if re.search(rf"(?<!\w){re.escape(name)}(?!\w)", text, re.IGNORECASE):
                candidates.append((f"{path}:text", "spell", name))
    return candidates


def _text_values(value, path="payload"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _text_values(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _text_values(child, f"{path}[{index}]")
    elif isinstance(value, str):
        yield path, value


def extract_reference_candidates(entity_type, payload):
    """Yield schema-backed reference paths, target types, and display names."""
    candidates = []
    if entity_type == "item":
        spells = (payload.get("magic_item") or {}).get("spells") or []
        candidates.extend(
            (f"magic_item.spells[{index}].spell", "spell", item["spell"])
            for index, item in enumerate(spells)
            if isinstance(item, dict) and isinstance(item.get("spell"), str)
        )
    if entity_type in {"feat", "race"}:
        for grant_index, grant in enumerate(payload.get("spell_grants") or []):
            for spell_index, spell in enumerate(grant.get("spells") or []):
                if isinstance(spell, str):
                    candidates.append(
                        (
                            f"spell_grants[{grant_index}].spells[{spell_index}]",
                            "spell",
                            spell,
                        )
                    )
    if entity_type == "class":
        grants = ((payload.get("spellcasting") or {}).get("spells") or [])
        candidates.extend(_spell_grant_names(grants, "spellcasting.spells"))
    if entity_type == "subclass":
        candidates.extend(_spell_grant_names(payload.get("spells") or [], "spells"))
    if entity_type == "monster":
        known = (payload.get("spell_casting") or {}).get("spells_known") or {}
        candidates.extend(_spell_names(known, "spell_casting.spells_known"))
    if entity_type in {"spell", "ability"}:
        for index, class_name in enumerate(payload.get("classes") or []):
            if isinstance(class_name, str):
                candidates.append((f"classes[{index}]", "class", class_name))
    return tuple(candidates)


def _spell_grant_names(grants, path):
    candidates = []
    if isinstance(grants, dict):
        grants = [grants]
    for grant_index, grant in enumerate(grants):
        if not isinstance(grant, dict):
            continue
        for spell_index, spell in enumerate(grant.get("spells") or []):
            if isinstance(spell, str):
                candidates.append(
                    (f"{path}[{grant_index}].spells[{spell_index}]", "spell", spell)
                )
    return candidates


def _spell_names(value, path):
    candidates = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            if key in {"spells", "cantrips", "at_will"} and isinstance(child, list):
                candidates.extend(
                    (f"{child_path}[{index}]", "spell", name)
                    for index, name in enumerate(child)
                    if isinstance(name, str)
                )
            else:
                candidates.extend(_spell_names(child, child_path))
    return candidates


def _entity_name(entity):
    return getattr(entity, "display_name", getattr(entity, "name", ""))


class EntityNavigationController:
    """Resolve canonical references while retaining reversible navigation context."""

    def __init__(self, project_controller, on_open=None):
        self.project_controller = project_controller
        self.on_open = on_open
        self._history = []
        self._cache = {}

    def open(self, reference, *, origin_uid=None):
        if reference.target_uid in self._history:
            raise ValueError(f"Circular entity navigation: {reference.target_uid}")
        entity = self._cache.get(reference.target_uid)
        if entity is None:
            entity = self.project_controller.resolve_entity_reference(reference)
            self._cache[reference.target_uid] = entity
        if origin_uid is not None:
            self._history.append(origin_uid)
        if self.on_open is not None:
            self.on_open(entity)
        return entity

    def back(self):
        if not self._history:
            return None
        entity_uid = self._history.pop()
        entity = self._cache.get(entity_uid)
        if entity is None:
            entity = self.project_controller.resolve_entity(entity_uid)
            self._cache[entity_uid] = entity
        if self.on_open is not None:
            self.on_open(entity)
        return entity