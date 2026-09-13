from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from projectfoundry import ArtifactStore

from application.imports import ImportedEntityRecord
from objects.entity_database import EntityDatabaseBlock, EntityDatabaseBlockData


@dataclass(frozen=True)
class EntityQueryRow:
    uid: str
    entity_type: str
    name: str
    source_identity: str
    source_namespace: str
    provenance: str
    source_metadata: dict[str, Any]
    payload: dict[str, Any]


@dataclass(frozen=True)
class MissingEntityRow:
    uid: str
    missing: bool = True


@dataclass(frozen=True)
class EntityQueryField:
    label: str
    expression: str
    value_type: str = "text"
    choices: tuple[str, ...] = ()


DAMAGE_TYPES = (
    "acid", "bludgeoning", "cold", "fire", "force", "lightning",
    "necrotic", "piercing", "poison", "psychic", "radiant", "slashing",
    "thunder",
)
RARITIES = ("common", "uncommon", "rare", "very_rare", "legendary", "artifact")
ITEM_CATEGORIES = (
    "armor", "potion", "ring", "rod", "scroll", "staff", "wand", "weapon",
    "wonderous_item", "adventuring_gear", "tool",
)
WEAPON_PROPERTIES = (
    "ammunition", "finesse", "heavy", "light", "loading", "monk", "reach",
    "special", "thrown", "two_handed", "versatile",
)
ARMOR_CATEGORIES = ("light", "medium", "heavy", "shield")
SPELL_SCHOOLS = (
    "abjuration", "chronomancy", "conjuration", "divination", "dunamancy",
    "enchantment", "evocation", "illusion", "necromancy", "transmutation",
)
SPELL_COMPONENTS = ("verbal", "somatic", "material")
CLASS_NAMES = (
    "artificer", "barbarian", "bard", "blood_hunter", "cleric", "druid",
    "fighter", "monk", "paladin", "ranger", "rogue", "sorcerer", "warlock",
    "wizard",
)
SIZES = ("tiny", "small", "medium", "large", "huge", "gargantuan")
CREATURE_TYPES = (
    "aberration", "beast", "celestial", "construct", "dragon", "elemental",
    "fey", "fiend", "giant", "humanoid", "monstrosity", "ooze", "plant",
    "undead",
)
CONDITIONS = (
    "blinded", "charmed", "deafened", "exhaustion", "frightened", "grappled",
    "incapacitated", "invisible", "paralyzed", "petrified", "poisoned", "prone",
    "restrained", "stunned", "unconscious",
)
ABILITY_SCORES = (
    "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma",
)
SKILLS = (
    "acrobatics", "animal_handling", "arcana", "athletics", "deception", "history",
    "insight", "intimidation", "investigation", "medicine", "nature", "perception",
    "performance", "persuasion", "religion", "sleight_of_hand", "stealth", "survival",
)


def _text(label, path):
    return EntityQueryField(label, f"json_extract(payload, '$.{path}')")


def _choice(label, path, choices):
    return EntityQueryField(
        label,
        f"json_extract(payload, '$.{path}')",
        choices=tuple(choices),
    )


def _number(label, path, number_type="float"):
    sql_type = "INTEGER" if number_type == "integer" else "REAL"
    return EntityQueryField(
        label,
        f"CAST(json_extract(payload, '$.{path}') AS {sql_type})",
        number_type,
    )


def _boolean(label, path):
    return EntityQueryField(
        label,
        f"CASE WHEN json_extract(payload, '$.{path}') THEN 1 ELSE 0 END",
        "boolean",
    )


def _present(label, path):
    return EntityQueryField(
        label,
        f"CASE WHEN json_type(payload, '$.{path}') IS NOT NULL THEN 1 ELSE 0 END",
        "boolean",
    )


def _nonempty_collection(label, path):
    return EntityQueryField(
        label,
        (
            f"CASE WHEN COALESCE(json_array_length(payload, '$.{path}'), 0) > 0 "
            "THEN 1 ELSE 0 END"
        ),
        "boolean",
    )


def _collection(label, path, choices=()):
    return EntityQueryField(
        label,
        f"json_extract(payload, '$.{path}')",
        "collection",
        tuple(choices),
    )


class EntityDatabaseStore:
    """Transactional SQLite source of truth for imported entity records."""

    SCHEMA_VERSION = 1
    QUERY_FIELDS = {
        "item": {
            "name": EntityQueryField("Name", "name"),
            "description": _text("Description", "description"),
            "category": _choice("Category", "category", ITEM_CATEGORIES),
            "weight": _number("Weight", "weight"),
            "cost": _number("Cost", "cost.amount"),
            "is_weapon": _present("Is a weapon", "weapon"),
            "weapon_type": _text("Weapon type", "weapon.type"),
            "weapon_property": _collection(
                "Weapon property", "weapon.properties", WEAPON_PROPERTIES
            ),
            "weapon_damage_type": _collection(
                "Weapon damage type", "weapon.effects", DAMAGE_TYPES
            ),
            "weapon_range": _number("Weapon normal range", "weapon.range.normal"),
            "is_armor": _present("Is armor", "armor"),
            "armor_category": _choice(
                "Armor category", "armor.category", ARMOR_CATEGORIES
            ),
            "armor_class": _number("Armor class", "armor.armor_class", "integer"),
            "requires_attunement": _boolean(
                "Requires attunement", "magic_item.attunement"
            ),
            "is_magic_item": _present("Is a magic item", "magic_item"),
            "rarity": EntityQueryField(
                "Rarity",
                "json_extract(payload, '$.magic_item.rarity')",
                choices=RARITIES,
            ),
            "grants_spells": _nonempty_collection(
                "Grants spells", "magic_item.spells"
            ),
            "granted_spell": _collection("Granted spell", "magic_item.spells"),
            "grant_type": _collection("Grant type", "magic_item.grants"),
            "granted_damage_type": _collection(
                "Granted damage type", "magic_item.grants", DAMAGE_TYPES
            ),
            "feature": _collection("Feature", "features"),
            "source": _collection("Source", "source"),
        },
        "spell": {
            "name": EntityQueryField("Name", "name"),
            "description": _text("Description", "description"),
            "higher_level": _text("At higher levels", "higher_level"),
            "level": _number("Level", "level", "integer"),
            "school": _choice("School", "school", SPELL_SCHOOLS),
            "class": _collection("Class", "classes", CLASS_NAMES),
            "component": _collection("Component", "components", SPELL_COMPONENTS),
            "ritual": _boolean("Ritual", "ritual"),
            "concentration": _boolean("Concentration", "concentration"),
            "casting_time_unit": _collection("Casting time", "casting_time"),
            "duration": _text("Duration", "duration.duration"),
            "tag": _collection("Tag", "tags"),
            "damage_type": _collection("Damage type", "effects", DAMAGE_TYPES),
            "grant_type": _collection("Grant type", "grants"),
            "source": _collection("Source", "source"),
        },
        "monster": {
            "name": EntityQueryField("Name", "name"),
            "description": _text("Description", "description"),
            "challenge_rating": _number("Challenge rating", "challenge_rating"),
            "size": _choice("Size", "size", SIZES),
            "creature_type": _choice(
                "Creature type", "creature_type", CREATURE_TYPES
            ),
            "alignment": _text("Alignment", "alignment"),
            "armor_class": _number("Armor class", "armor_class.value", "integer"),
            "passive_perception": _number(
                "Passive perception", "passive_perception", "integer"
            ),
            "language": _collection("Language", "languages"),
            "condition_immunity": _collection(
                "Condition immunity", "condition_immunities", CONDITIONS
            ),
            "damage_immunity": _collection(
                "Damage immunity", "damage_immunities", DAMAGE_TYPES
            ),
            "damage_resistance": _collection(
                "Damage resistance", "damage_resistances", DAMAGE_TYPES
            ),
            "damage_vulnerability": _collection(
                "Damage vulnerability", "damage_vulnerabilities", DAMAGE_TYPES
            ),
            "environment": _collection("Environment", "environments"),
            "casts_spell": _collection("Casts spell", "spell_casting.spells_known"),
            "feature": _collection("Feature", "features"),
            "action": _collection("Action", "actions"),
            "source": _collection("Source", "source"),
        },
        "race": {
            "name": EntityQueryField("Name", "name"),
            "subtype": _text("Subtype", "subtype"),
            "size": _choice("Size", "size", SIZES),
            "language": _collection("Language", "languages"),
            "skill_proficiency": _collection(
                "Skill proficiency", "skill_proficiencies", SKILLS
            ),
            "weapon_proficiency": _collection(
                "Weapon proficiency", "weapon_proficiencies"
            ),
            "armor_proficiency": _collection(
                "Armor proficiency", "armor_proficiencies"
            ),
            "granted_spell": _collection("Granted spell", "spell_grants"),
            "granted_feat": _collection("Granted feat", "feats"),
            "movement": _collection("Movement", "movement"),
            "ability_score_increase": _collection(
                "Ability score increase", "ability_score_increases"
            ),
            "feature": _collection("Feature", "features"),
            "source": _collection("Source", "source"),
        },
        "class": {
            "name": EntityQueryField("Name", "name"),
            "description": _text("Description", "description"),
            "hit_dice": _collection("Hit dice", "hit_dice"),
            "primary_ability": _collection(
                "Primary ability", "primary_abilities", ABILITY_SCORES
            ),
            "saving_throw": _collection(
                "Saving throw", "saving_throws", ABILITY_SCORES
            ),
            "armor_proficiency": _collection(
                "Armor proficiency", "armor_proficiencies"
            ),
            "weapon_proficiency": _collection(
                "Weapon proficiency", "weapon_proficiencies"
            ),
            "tool_proficiency": _collection("Tool proficiency", "tool_proficiencies"),
            "skill_choice": _collection("Skill choice", "skill_choices"),
            "has_spellcasting": _present("Has spellcasting", "spellcasting"),
            "subclass_level": _number("Subclass level", "subclass_level", "integer"),
            "feature": _collection("Feature", "features"),
            "tag": _collection("Tag", "tags"),
            "source": _collection("Source", "source"),
        },
        "subclass": {
            "name": EntityQueryField("Name", "name"),
            "class": _choice("Class", "class", CLASS_NAMES),
            "description": _text("Description", "description"),
            "feature": _collection("Feature", "features"),
            "granted_spell": _collection("Granted spell", "spells"),
            "tag": _collection("Tag", "tags"),
            "source": _collection("Source", "source"),
        },
        "feat": {
            "name": EntityQueryField("Name", "name"),
            "description": _text("Description", "description"),
            "prerequisite": _text("Prerequisite", "prerequisite"),
            "skill_proficiency": _collection(
                "Skill proficiency", "skill_proficiencies", SKILLS
            ),
            "weapon_proficiency": _collection(
                "Weapon proficiency", "weapon_proficiencies"
            ),
            "armor_proficiency": _collection(
                "Armor proficiency", "armor_proficiencies"
            ),
            "granted_spell": _collection("Granted spell", "spell_grants"),
            "tag": _collection("Tag", "tags"),
            "tool_proficiency": _collection("Tool proficiency", "tool_proficiencies"),
            "vehicle_proficiency": _collection(
                "Vehicle proficiency", "vehicle_proficiencies"
            ),
            "feature": _collection("Feature", "features"),
            "action": _collection("Action", "actions"),
            "source": _collection("Source", "source"),
        },
        "background": {
            "name": EntityQueryField("Name", "name"),
            "description": _text("Description", "description"),
            "skill_proficiency": _collection(
                "Skill proficiency", "skill_proficiencies", SKILLS
            ),
            "tool_proficiency": _collection("Tool proficiency", "tool_proficiencies"),
            "language": _collection("Language", "languages"),
            "feature": _collection("Feature", "features"),
            "equipment": _collection("Equipment", "equipment"),
            "tag": _collection("Tag", "tags"),
            "source": _collection("Source", "source"),
        },
        "ability": {
            "name": EntityQueryField("Name", "name"),
            "description": _text("Description", "description"),
            "kind": EntityQueryField(
                "Kind",
                "json_extract(payload, '$.kind')",
                choices=(
                    "maneuver", "eldritch_invocation", "infusion",
                    "monk_technique", "other",
                ),
            ),
            "level": _number("Level", "level", "integer"),
            "class": _collection("Class", "classes", CLASS_NAMES),
            "prerequisite": _collection("Prerequisite", "prerequisites"),
            "source": _collection("Source", "source"),
        },
    }
    FIELD_PROJECTIONS = {
        entity_type: {
            name: definition.expression for name, definition in definitions.items()
        }
        for entity_type, definitions in QUERY_FIELDS.items()
    }
    OPERATORS = {
        "eq": "=",
        "ne": "!=",
        "lt": "<",
        "lte": "<=",
        "gt": ">",
        "gte": ">=",
        "contains": "LIKE",
        "has": "HAS",
        "not_has": "NOT HAS",
        "any_of": "IN",
        "none_of": "NOT IN",
    }

    def __init__(self, database_path, *, namespace="compendium", block=None):
        self.database_path = Path(database_path)
        self.namespace = namespace
        self.block = block or EntityDatabaseBlock(
            f"{namespace.title()} Entities",
            namespace=namespace,
        )

    def connect(self):
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def require_json1(connection):
        try:
            valid, extracted = connection.execute(
                "SELECT json_valid(?), json_extract(?, '$.value')",
                ('{}', '{"value": 1}'),
            ).fetchone()
        except sqlite3.Error as error:
            raise RuntimeError("SQLite JSON1 support is required") from error
        if valid != 1 or extracted != 1:
            raise RuntimeError("SQLite JSON1 support is required")

    def initialize(self):
        with closing(self.connect()) as connection, connection:
            self.require_json1(connection)
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS entity_store_metadata (
                    schema_version INTEGER NOT NULL
                );
                INSERT INTO entity_store_metadata(schema_version)
                    SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM entity_store_metadata);
                CREATE TABLE IF NOT EXISTS entities (
                    uid TEXT PRIMARY KEY,
                    source_identity TEXT NOT NULL UNIQUE,
                    entity_type TEXT NOT NULL,
                    name TEXT NOT NULL,
                    source_namespace TEXT NOT NULL,
                    provenance TEXT NOT NULL,
                    source_metadata TEXT NOT NULL CHECK (json_valid(source_metadata)),
                    payload TEXT NOT NULL CHECK (json_valid(payload))
                );
                CREATE INDEX IF NOT EXISTS idx_entities_type_name
                    ON entities(entity_type, name COLLATE NOCASE);
                CREATE INDEX IF NOT EXISTS idx_entities_item_weight
                    ON entities(CAST(json_extract(payload, '$.weight') AS REAL))
                    WHERE entity_type = 'item';
                CREATE INDEX IF NOT EXISTS idx_entities_spell_level
                    ON entities(CAST(json_extract(payload, '$.level') AS INTEGER))
                    WHERE entity_type = 'spell';
                CREATE INDEX IF NOT EXISTS idx_entities_monster_cr
                    ON entities(json_extract(payload, '$.challenge_rating'))
                    WHERE entity_type = 'monster';
                """
            )
        self._sync_block_metadata()
        return self

    def commit_records(self, records, *, duplicate_policy="reject"):
        if duplicate_policy not in {"reject", "skip", "replace", "merge"}:
            raise ValueError(f"Unsupported duplicate policy: {duplicate_policy}")
        records = tuple(records)
        with closing(self.connect()) as connection, connection:
            self.require_json1(connection)
            for record in records:
                self._validate_record_namespace(record)
                values = self._record_values(record)
                if duplicate_policy == "reject":
                    connection.execute(self._insert_sql(), values)
                elif duplicate_policy == "skip":
                    connection.execute(
                        self._insert_sql().replace("INSERT", "INSERT OR IGNORE", 1),
                        values,
                    )
                elif duplicate_policy == "replace":
                    connection.execute(self._upsert_sql(), values)
                else:
                    existing = connection.execute(
                        "SELECT payload FROM entities WHERE source_identity = ?",
                        (record.source_identity,),
                    ).fetchone()
                    if existing is not None:
                        payload = json.loads(existing["payload"])
                        payload.update(record.payload)
                        values = (*values[:-1], json.dumps(payload, separators=(",", ":")))
                    connection.execute(self._upsert_sql(), values)
        self._sync_block_metadata()
        return self.count()

    def query(
        self,
        entity_type,
        *,
        field="name",
        operator="eq",
        value=None,
        criteria=None,
        sort_field="name",
        sort_order="asc",
        limit=100,
    ):
        fields = self.FIELD_PROJECTIONS.get(entity_type)
        if fields is None:
            raise ValueError(f"Unsupported entity type: {entity_type}")
        try:
            sort_expression = fields[sort_field]
        except KeyError as error:
            raise ValueError(
                f"Unsupported sort field for {entity_type}: {sort_field}"
            ) from error
        if sort_order not in {"asc", "desc"}:
            raise ValueError(f"Unsupported sort order: {sort_order}")
        if not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("Query limit must be between 1 and 1000")
        parameters = [entity_type]
        where = "entity_type = ?"
        conditions = (
            tuple(criteria)
            if criteria is not None
            else ((field, operator, value),)
        )
        for condition_field, condition_operator, condition_value in conditions:
            if condition_operator == "all":
                continue
            try:
                expression = fields[condition_field]
            except KeyError as error:
                raise ValueError(
                    f"Unsupported field for {entity_type}: {condition_field}"
                ) from error
            try:
                sql_operator = self.OPERATORS[condition_operator]
            except KeyError as error:
                raise ValueError(
                    f"Unsupported query operator: {condition_operator}"
                ) from error
            if condition_operator in {"any_of", "none_of"}:
                if isinstance(condition_value, (str, bytes)):
                    raise ValueError("Multi-value query requires a sequence of values")
                values = tuple(condition_value)
                if not values:
                    raise ValueError("Multi-value query requires at least one value")
                placeholders = ", ".join("?" for _value in values)
                definition = self.QUERY_FIELDS[entity_type][condition_field]
                if definition.value_type == "collection":
                    clause = (
                        "EXISTS (SELECT 1 FROM json_tree(" + expression + ") "
                        f"WHERE atom IN ({placeholders}))"
                    )
                else:
                    clause = f"{expression} IN ({placeholders})"
                if condition_operator == "none_of":
                    clause = f"NOT ({clause})"
                where += f" AND {clause}"
                parameters.extend(values)
                continue
            if condition_operator in {"has", "not_has"}:
                clause = (
                    "EXISTS (SELECT 1 FROM json_tree(" + expression + ") "
                    "WHERE atom = ?)"
                )
                if condition_operator == "not_has":
                    clause = f"NOT ({clause})"
                where += f" AND {clause}"
                parameters.append(condition_value)
                continue
            if condition_operator == "contains":
                condition_value = f"%{condition_value}%"
            where += f" AND {expression} {sql_operator} ?"
            parameters.append(condition_value)
        parameters.append(limit)
        sql = (
            "SELECT uid, entity_type, name, source_identity, source_namespace, "
            "provenance, source_metadata, payload FROM entities "
            f"WHERE {where} ORDER BY {sort_expression} {sort_order.upper()}, "
            "name COLLATE NOCASE, uid LIMIT ?"
        )
        with closing(self.connect()) as connection:
            self.require_json1(connection)
            rows = connection.execute(sql, parameters).fetchall()
        return tuple(
            EntityQueryRow(
                uid=row["uid"],
                entity_type=row["entity_type"],
                name=row["name"],
                source_identity=row["source_identity"],
                source_namespace=row["source_namespace"],
                provenance=row["provenance"],
                source_metadata=json.loads(row["source_metadata"]),
                payload=json.loads(row["payload"]),
            )
            for row in rows
        )

    def count(self):
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT COUNT(*) FROM entities").fetchone()
        return row[0]

    def all_records(self):
        """Return every canonical entity for durable namespace export."""
        with closing(self.connect()) as connection:
            rows = connection.execute(
                "SELECT uid, entity_type, name, source_identity, source_namespace, "
                "provenance, source_metadata, payload FROM entities "
                "ORDER BY name COLLATE NOCASE, uid"
            ).fetchall()
        return tuple(
            EntityQueryRow(
                uid=row["uid"],
                entity_type=row["entity_type"],
                name=row["name"],
                source_identity=row["source_identity"],
                source_namespace=row["source_namespace"],
                provenance=row["provenance"],
                source_metadata=json.loads(row["source_metadata"]),
                payload=json.loads(row["payload"]),
            )
            for row in rows
        )

    def source_identities(self):
        with closing(self.connect()) as connection:
            rows = connection.execute("SELECT source_identity FROM entities").fetchall()
        return {row[0] for row in rows}

    def get(self, entity_uid):
        with closing(self.connect()) as connection:
            row = connection.execute(
                "SELECT uid, entity_type, name, source_identity, source_namespace, "
                "provenance, source_metadata, payload "
                "FROM entities WHERE uid = ?",
                (entity_uid,),
            ).fetchone()
        if row is None:
            return None
        return EntityQueryRow(
            uid=row["uid"],
            entity_type=row["entity_type"],
            name=row["name"],
            source_identity=row["source_identity"],
            source_namespace=row["source_namespace"],
            provenance=row["provenance"],
            source_metadata=json.loads(row["source_metadata"]),
            payload=json.loads(row["payload"]),
        )

    def delete(self, entity_uid):
        """Delete one entity row without affecting another source namespace."""
        with closing(self.connect()) as connection, connection:
            cursor = connection.execute(
                "DELETE FROM entities WHERE uid = ? AND source_namespace = ?",
                (entity_uid, self.namespace),
            )
            if cursor.rowcount != 1:
                raise ValueError(f"Unknown {self.namespace} entity UID: {entity_uid}")
        self._sync_block_metadata()

    def _validate_record_namespace(self, record):
        if not isinstance(record, ImportedEntityRecord):
            raise TypeError("Entity database accepts ImportedEntityRecord values")
        if self.namespace not in {"compendium", "homebrew"}:
            raise ValueError(f"Unsupported entity namespace: {self.namespace}")

    def _sync_block_metadata(self):
        checksum = ArtifactStore.checksum(self.database_path) if self.database_path.is_file() else None
        artifact = self.block.block_data.artifact.model_copy(
            update={"checksum": checksum, "valid": checksum is not None}
        )
        self.block.block_data = EntityDatabaseBlockData(
            artifact=artifact,
            namespace=self.namespace,
            schema_version=self.SCHEMA_VERSION,
            row_count=self.count() if self.database_path.is_file() else 0,
        )

    def _record_values(self, record):
        return (
            record.uid,
            record.source_identity,
            record.entity_type,
            record.display_name,
            self.namespace,
            record.provenance,
            json.dumps(record.source_metadata, separators=(",", ":")),
            json.dumps(record.payload, separators=(",", ":")),
        )

    @staticmethod
    def _insert_sql():
        return (
            "INSERT INTO entities "
            "(uid, source_identity, entity_type, name, source_namespace, provenance, source_metadata, payload) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
        )

    @classmethod
    def _upsert_sql(cls):
        return cls._insert_sql() + (
            " ON CONFLICT(source_identity) DO UPDATE SET "
            "uid=excluded.uid, entity_type=excluded.entity_type, name=excluded.name, "
            "source_namespace=excluded.source_namespace, provenance=excluded.provenance, "
            "source_metadata=excluded.source_metadata, payload=excluded.payload"
        )