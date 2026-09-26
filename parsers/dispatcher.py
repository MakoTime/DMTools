from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Type

from pydantic import BaseModel

from models.ability import Ability
from models.background import Background
from models.class_model import Class
from models.feat import Feat
from models.item import Item
from models.monster import Monster
from models.race import Race
from models.spell import Spell

from .background_adaptor import BackgroundAdaptor
from .background_parser import parse_background
from .class_adaptor import ClassAdaptor
from .class_parser import parse_class
from .ability_adaptor import AbilityAdaptor
from .ability_parser import parse_ability
from .feat_adaptor import FeatAdaptor
from .feat_parser import parse_feat
from .item_adaptor import ItemAdaptor
from .item_parser import parse_item
from .monster_adaptor import MonsterAdaptor
from .monster_parser import parse_monster
from .race_adaptor import RaceAdaptor
from .race_parser import parse_race
from .spell_adaptor import SpellAdaptor
from .spell_parser import parse_spell


@dataclass(frozen=True)
class EntityHandler:
    parser: Callable[[dict[str, Any]], dict[str, Any]]
    adaptor: Any
    model: Type[BaseModel]
    schema: str


ABILITY_HANDLER = EntityHandler(
    parse_ability,
    AbilityAdaptor(),
    Ability,
    "Ability.schema.json",
)


HANDLERS = {
    "item": EntityHandler(parse_item, ItemAdaptor(), Item, "Item.schema.json"),
    "monster": EntityHandler(parse_monster, MonsterAdaptor(), Monster, "Monster.schema.json"),
    "spell": EntityHandler(parse_spell, SpellAdaptor(), Spell, "Spell.schema.json"),
    "race": EntityHandler(parse_race, RaceAdaptor(), Race, "Race.schema.json"),
    "feat": EntityHandler(parse_feat, FeatAdaptor(), Feat, "Feat.schema.json"),
    "background": EntityHandler(parse_background, BackgroundAdaptor(), Background, "Background.schema.json"),
    "class": EntityHandler(parse_class, ClassAdaptor(), Class, "Class.schema.json"),
}


def dispatch_element(element: dict[str, Any]) -> dict[str, Any]:
    tag = element.get("tag")
    handler = HANDLERS.get(tag)
    if handler is None:
        return {
            "tag": tag,
            "name": get_name(element),
            "status": "unsupported",
            "error": f"Unsupported entity tag: {tag}",
        }

    raw = handler.parser(element)
    result_tag = tag
    if tag == "spell" and AbilityAdaptor.is_custom_ability(raw):
        handler = ABILITY_HANDLER
        result_tag = "ability"
    adapted = handler.adaptor.adapt(raw)
    result = {
        "tag": result_tag,
        "name": get_name(element),
        "status": "success",
        "raw": raw,
        "data": adapted,
    }
    if tag == "class":
        result["source_metadata"] = {
            "subclass_feature_levels": ClassAdaptor().subclass_feature_levels(raw),
            "subclass_progression": ClassAdaptor().subclass_progression(raw),
            "presentation_progression": {
                "cantrips_known": ClassAdaptor().cantrips_known(raw),
                "resources": ClassAdaptor().resource_progression(raw),
            },
        }
    return result


def dispatch_root(
    root: dict[str, Any],
    *,
    is_cancelled: Callable[[], bool] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> list[dict[str, Any]]:
    results = []
    elements = root.get("children", [])
    total = len(elements)
    for index, element in enumerate(elements):
        if is_cancelled is not None and is_cancelled():
            break
        if progress_callback is not None:
            progress_callback(index, total)
        try:
            result = dispatch_element(element)
            results.append(result)
            if element.get("tag") == "class":
                results.extend(dispatch_subclasses(element))
        except Exception as error:
            results.append({
                "tag": element.get("tag"),
                "name": get_name(element),
                "status": "failed",
                "error": str(error),
            })
    if progress_callback is not None:
        progress_callback(total, total)
    return results


def dispatch_subclasses(element: dict[str, Any]) -> list[dict[str, Any]]:
    source = parse_class(element)
    records = []
    for data in ClassAdaptor().subclasses(source):
        try:
            records.append({
                "tag": "subclass",
                "name": data["name"],
                "status": "success",
                "data": data,
            })
        except Exception as error:
            records.append({
                "tag": "subclass",
                "name": data.get("name"),
                "status": "failed",
                "error": str(error),
            })
    return records


def get_name(element: dict[str, Any]) -> str | None:
    for child in element.get("children", []):
        if child.get("tag") == "name":
            return child.get("text")
    return None