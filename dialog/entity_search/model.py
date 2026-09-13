from dataclasses import dataclass, field

from dialog.base.editor import EditorModel


@dataclass(frozen=True)
class SearchCriterion:
    field: str
    operator: str
    value: object


@dataclass
class EntitySearchModel(EditorModel):
    """Temporary criteria and results for one entity-category search."""

    store: object
    entity_type: str
    criteria: list[SearchCriterion] = field(default_factory=list)
    rows: tuple = field(default_factory=tuple)

    OPERATOR_LABELS = {
        "contains": "contains",
        "eq": "equals",
        "ne": "does not equal",
        "lt": "is less than",
        "lte": "is at most",
        "gt": "is greater than",
        "gte": "is at least",
        "has": "contains",
        "not_has": "does not contain",
        "any_of": "is any of",
        "none_of": "is none of",
    }

    @property
    def fields(self):
        try:
            return tuple(self.store.FIELD_PROJECTIONS[self.entity_type])
        except KeyError as error:
            raise ValueError(f"Unsupported entity type: {self.entity_type}") from error

    def field_definition(self, field_name):
        definitions = getattr(self.store, "QUERY_FIELDS", {}).get(self.entity_type, {})
        return definitions.get(field_name)

    def field_label(self, field_name):
        definition = self.field_definition(field_name)
        return definition.label if definition else field_name.replace("_", " ").title()

    def value_type_for(self, field_name):
        definition = self.field_definition(field_name)
        if definition is not None:
            return definition.value_type
        return "integer" if field_name == "level" else (
            "float" if field_name in {"weight", "challenge_rating"} else "text"
        )

    def choices_for(self, field_name):
        definition = self.field_definition(field_name)
        return definition.choices if definition else ()

    def operators_for(self, field_name):
        if self.choices_for(field_name):
            return ("any_of", "none_of")
        value_type = self.value_type_for(field_name)
        if value_type == "collection":
            return ("has", "not_has")
        if value_type == "boolean":
            return ("eq",)
        if value_type in {"integer", "float"}:
            return ("eq", "ne", "lt", "lte", "gt", "gte")
        return ("contains", "eq", "ne")

    def add_criterion(self, field_name, operator, value):
        if field_name not in self.fields:
            raise ValueError(f"Unsupported field for {self.entity_type}: {field_name}")
        if operator not in self.operators_for(field_name):
            raise ValueError(f"Unsupported operator for {field_name}: {operator}")
        choices = self.choices_for(field_name)
        if choices:
            values = tuple(value) if not isinstance(value, str) else (value,)
            if not values:
                raise ValueError("Select at least one value for the search parameter.")
            invalid = [item for item in values if item not in choices]
            if invalid:
                raise ValueError(f"Unsupported value for {field_name}: {invalid[0]}")
            criterion = SearchCriterion(field_name, operator, values)
            self.criteria.append(criterion)
            return criterion
        value_type = self.value_type_for(field_name)
        text = str(value).strip()
        if value_type != "boolean" and not text:
            raise ValueError("Enter a value for the search parameter.")
        converters = {"integer": int, "float": float, "boolean": self._boolean_value}
        converter = converters.get(value_type, str)
        try:
            converted_value = converter(text)
        except ValueError as error:
            raise ValueError(f"Enter a valid value for {field_name.replace('_', ' ')}.") from error
        self.criteria.append(SearchCriterion(field_name, operator, converted_value))
        return self.criteria[-1]

    @staticmethod
    def _boolean_value(value):
        if isinstance(value, bool):
            return int(value)
        normalized = str(value).strip().casefold()
        if normalized in {"true", "yes", "1"}:
            return 1
        if normalized in {"false", "no", "0"}:
            return 0
        raise ValueError

    def remove_criterion(self, index):
        if 0 <= index < len(self.criteria):
            return self.criteria.pop(index)
        return None

    def execute(self):
        self.validate()
        self.rows = self.store.query(
            self.entity_type,
            criteria=tuple(
                (criterion.field, criterion.operator, criterion.value)
                for criterion in self.criteria
            ),
        )
        return self.rows

    def release_results(self):
        self.rows = ()

    def validate(self):
        for criterion in self.criteria:
            if criterion.field not in self.fields:
                raise ValueError(
                    f"Unsupported field for {self.entity_type}: {criterion.field}"
                )

    def apply(self):
        self.execute()
        return self
