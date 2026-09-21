from .model import RuleDetailModel
from .view import RuleDetailView


def create_rule_detail_dialog(value, category, schema_names, parent=None):
    return RuleDetailView(
        RuleDetailModel(value, category, tuple(schema_names)),
        parent=parent,
    )