from .model import RuleDetailModel
from .view import RuleDetailView


def create_rule_detail_dialog(
    value,
    category,
    schema_names,
    parent=None,
    related_entities=(),
    on_entity_link=None,
):
    return RuleDetailView(
        RuleDetailModel(
            value, category, tuple(schema_names), tuple(related_entities)
        ),
        parent=parent,
        on_entity_link=on_entity_link,
    )