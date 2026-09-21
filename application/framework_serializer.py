from projectfoundry.core.serialization import ProjectSerializer


class DMToolsFrameworkSerializer(ProjectSerializer):
    """ProjectFoundry serializer preserving DMTools structural node metadata."""

    @classmethod
    def _tree_record(cls, project, node):
        record = super()._tree_record(project, node)
        for field in (
            "node_type",
            "namespace",
            "entity_type",
            "category_type",
            "value",
            "schema_names",
            "entity_uid",
            "protected",
        ):
            value = getattr(node, field, None)
            if value is not None:
                record[field] = value
        return record

    @staticmethod
    def _restore_tree(records, project):
        ProjectSerializer._restore_tree(records, project)
        for record in records:
            node = project.nodes.get(record["node_uid"])
            for field in (
                "node_type",
                "namespace",
                "entity_type",
                "category_type",
                "value",
                "schema_names",
                "entity_uid",
                "protected",
            ):
                if field in record:
                    setattr(node, field, record[field])