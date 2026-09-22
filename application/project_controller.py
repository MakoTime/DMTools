from pathlib import Path
import json

from projectfoundry import (
    Project,
    ProjectContext,
    ProjectService,
    QtTaskRunner,
    SerializerRegistry,
    TaskRunner,
)
from projectfoundry.tree import TreeModel as ProjectTreeModel
from PySide6.QtWidgets import QDialog, QFileDialog

from application.framework_serializer import DMToolsFrameworkSerializer
from application.project_serializer import ProjectSerializer
from application.project_lifecycle import ProjectLifecycleService
from application.project_tree import ProjectTreeMutationService
from application.legacy_tree_projection import LegacyTreeProjectionAdapter
from components.tree import TreeManager, TreeModel
from components.tree.roots.db_root import database_root
from components.tree.roots.entity_roots import (
    compendium_root,
    custom_rule_values,
    homebrew_root,
)
from components.tree.roots.root_objects import root_objects


class ProjectController:
    """Own the tree manager/model and drive project save/load/open.

    This is deliberately decoupled from any specific main window - wire its
    ``tree_model`` into a ``TreeView`` and call the save/open methods from
    menu actions once the application window exists.
    """

    def __init__(self, duplicate_name_dialog=None, artifact_store=None):
        root_objects.reset()
        self._artifact_store = artifact_store
        self.project = Project(artifact_store=artifact_store)
        self.task_runner = QtTaskRunner(TaskRunner(project=self.project))
        self.project_context = None
        self.project_service = ProjectService(
            self.project, task_runner=self.task_runner
        )
        self.tree_mutations = ProjectTreeMutationService(self.project)
        self.tree_projection = LegacyTreeProjectionAdapter(self.project)
        self.framework_registry = SerializerRegistry()
        self.framework_registry.register_block("database", self._database_block_from_record)
        self.framework_registry.register_block("query", self._query_block_from_record)
        self.framework_registry.register_block("json", self._json_block_from_record)
        self.framework_registry.register_block("table", self._table_block_from_record)
        self.framework_registry.register_block(
            "entity_database", self._entity_database_block_from_record
        )
        self.framework_registry.register_block(
            "entity_saved_query", self._entity_query_block_from_record
        )
        self.framework_registry.register_block("collection", self._collection_block_from_record)
        self.framework_registry.register_block(
            "shopkeeper", self._shopkeeper_block_from_record
        )
        self.framework_serializer = DMToolsFrameworkSerializer(self.framework_registry)
        self.project_serializer = ProjectSerializer()
        self.lifecycle_service = ProjectLifecycleService(
            self.project_serializer,
            self.framework_serializer,
        )
        self.project_tree_manager = self.project.tree
        self.project_tree_model = ProjectTreeModel(
            self.project_tree_manager.root_nodes,
            project=None,
        )
        self.tree_manager = TreeManager()
        self.tree_manager.root_nodes = root_objects.get_nodes()
        self.tree_model = TreeModel(
            self.tree_manager.root_nodes,
            duplicate_name_handler=self._resolve_duplicate_name,
            rename_handler=self._rename_tree_object,
        )
        self.project_file = None
        self._duplicate_name_dialog = duplicate_name_dialog
        self._project_replacement_callbacks = []
        self.refresh_project_tree()

    def add_project_replacement_callback(self, callback):
        if callback not in self._project_replacement_callbacks:
            self._project_replacement_callbacks.append(callback)

    def _notify_project_replacement(self):
        for callback in tuple(self._project_replacement_callbacks):
            callback()

    @staticmethod
    def _database_block_from_record(record):
        from objects.database_object import DatabaseBlock

        data = record.get("data", {})
        return DatabaseBlock(
            record["name"],
            database_path=data.get("database_path"),
            queries=data.get("queries", []),
            guid=record["block_uid"],
        )

    @staticmethod
    def _query_block_from_record(record):
        from objects.query_object import QueryBlock

        data = record.get("data", {})
        return QueryBlock(
            record["name"],
            database_guid=data.get("database_guid"),
            sql=data.get("sql", ""),
            table_name=data.get("table_name", ""),
            filters=data.get("filters", []),
            lookup=data.get("lookup", {}),
            guid=record["block_uid"],
        )

    @staticmethod
    def _json_block_from_record(record):
        from objects.json_object import JSONBlock

        data = record.get("data", {})
        return JSONBlock(
            record["name"],
            data=data.get("data", {}),
            guid=record["block_uid"],
        )

    @staticmethod
    def _table_block_from_record(record):
        from objects.table_object import TableBlock

        data = record.get("data", {})
        return TableBlock(
            record["name"],
            row_count=data.get("row_count", 0),
            columns=data.get("columns", []),
            artifact=data.get("artifact"),
            guid=record["block_uid"],
        )

    @staticmethod
    def _entity_database_block_from_record(record):
        from objects.entity_database import EntityDatabaseBlock

        data = record.get("data", {})
        return EntityDatabaseBlock(
            record["name"],
            namespace=data["namespace"],
            schema_version=data.get("schema_version", 1),
            row_count=data.get("row_count", 0),
            artifact=data.get("artifact"),
            guid=record["block_uid"],
        )

    @staticmethod
    def _entity_query_block_from_record(record):
        from objects.entity_query import EntityQueryBlock

        data = record.get("data", {})
        return EntityQueryBlock(
            record["name"],
            database_uid=data["database_uid"],
            entity_type=data["entity_type"],
            field=data.get("field", "name"),
            operator=data.get("operator", "all"),
            value=data.get("value"),
            sort_field=data.get("sort_field", "name"),
            sort_order=data.get("sort_order", "asc"),
            projection=data.get("projection", ["name"]),
            format_version=data.get("format_version", 1),
            guid=record["block_uid"],
        )

    @staticmethod
    def _collection_block_from_record(record):
        from objects.collection import CollectionBlock

        data = record.get("data", {})
        return CollectionBlock(
            record["name"],
            description=data.get("description", ""),
            entity_uids=data.get("entity_uids", []),
            dynamic_query_uid=data.get("dynamic_query_uid"),
            guid=record["block_uid"],
        )

    @staticmethod
    def _shopkeeper_block_from_record(record):
        from objects.shopkeeper_object import ShopkeeperBlock

        data = record.get("data", {})
        return ShopkeeperBlock(
            record["name"],
            database_uid=data.get("database_uid"),
            query_uids=data.get("query_uids", []),
            filters=data.get("filters", {}),
            stock_count=data.get("stock_count", 10),
            random_seed=data.get("random_seed"),
            guid=record["block_uid"],
        )

    def framework_project_document(self):
        """Return the transitional ProjectFoundry document for this project."""
        return self.framework_serializer.project_document(self.project)

    def entity_database_store(self, namespace="compendium"):
        """Create or open a project-owned entity database through its block."""
        from application.entity_database import EntityDatabaseStore
        from objects.entity_database import EntityDatabaseBlock

        if namespace not in {"compendium", "homebrew"}:
            raise ValueError(f"Unsupported entity namespace: {namespace}")
        if self.project.artifact_store is None:
            raise RuntimeError("Project has no artifact store")
        block_uid = f"dmtools-{namespace}-entity-database"
        if self.project.blocks.contains(block_uid):
            block = self.project.blocks.get(block_uid)
            if not isinstance(block, EntityDatabaseBlock):
                raise ValueError("Reserved entity database UID has another block type")
        else:
            block = EntityDatabaseBlock(
                f"{namespace.title()} Entities",
                namespace=namespace,
            )
            self.project.add_block(block)
            self.refresh_project_tree()
        path = self.project.artifact_store.path_for(block.block_data.artifact.path)
        return EntityDatabaseStore(path, namespace=namespace, block=block).initialize()

    def entity_source_identities(self, namespace="compendium"):
        """Return persisted source identities without creating a database block."""
        block_uid = f"dmtools-{namespace}-entity-database"
        if not self.project.blocks.contains(block_uid):
            return set()
        return self.entity_database_store(namespace).source_identities()

    def entity_source_records(self, namespace="compendium"):
        """Return persisted entity rows for import reference resolution."""
        block_uid = f"dmtools-{namespace}-entity-database"
        if not self.project.blocks.contains(block_uid):
            return ()
        return tuple(self.entity_database_store(namespace).all_records())

    def save_entity_namespace_json(self, namespace="compendium"):
        """Write a shareable JSON projection of the canonical entity store."""
        if namespace not in {"compendium", "homebrew"}:
            raise ValueError(f"Unsupported entity namespace: {namespace}")
        if self.project_file is None:
            return None
        store = self.entity_database_store(namespace)
        records = {}
        for row in store.all_records():
            records[row.uid] = {
                "uid": row.uid,
                "entity_type": row.entity_type,
                "name": row.name,
                "source_identity": row.source_identity,
                "source_namespace": row.source_namespace,
                "provenance": row.provenance,
                "source_metadata": row.source_metadata,
                "payload": row.payload,
            }
        directory = Path(self.project_file).parent / "data"
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / f"{namespace}.json"
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(records, indent=2), encoding="utf-8")
        temporary.replace(path)
        return path

    def prepare_imported_entities(self, records, *, namespace="compendium"):
        """Validate and normalize records before the persistence task runs."""
        from application.entity_references import normalize_entity_references

        records = tuple(records)
        root = compendium_root if namespace == "compendium" else homebrew_root
        for record in records:
            root.category(record.entity_type).validate_entity_type(record.entity_type)
        existing_entities = []
        for existing_namespace in ("compendium", "homebrew"):
            block_uid = f"dmtools-{existing_namespace}-entity-database"
            if not self.project.blocks.contains(block_uid):
                continue
            existing_store = self.entity_database_store(existing_namespace)
            for entity_type in existing_store.FIELD_PROJECTIONS:
                existing_entities.extend(
                    existing_store.query(entity_type, operator="all", limit=1000)
                )
        return normalize_entity_references(
            records,
            existing_entities,
            source_namespace=namespace,
        )

    def normalize_entity_references(self, parent=None, *, progress_factory=None):
        """Rebuild stored entity references with visible progress feedback."""
        from application.entity_references import normalize_entity_references
        from application.imports import ImportedEntityRecord

        if progress_factory is None:
            from dialog.import_progress.factory import create_import_task_progress

            progress_factory = create_import_task_progress

        records_by_namespace = {}
        existing_entities = []
        for namespace in ("compendium", "homebrew"):
            if not self.project.blocks.contains(
                f"dmtools-{namespace}-entity-database"
            ):
                continue
            records = []
            for row in self.entity_database_store(namespace).all_records():
                metadata = dict(row.source_metadata)
                metadata.pop("entity_references", None)
                metadata.pop("reference_diagnostics", None)
                records.append(
                    ImportedEntityRecord(
                        entity_type=row.entity_type,
                        uid=row.uid,
                        source_identity=row.source_identity,
                        display_name=row.name,
                        payload=row.payload,
                        source_metadata=metadata,
                        provenance=row.provenance,
                    )
                )
            records_by_namespace[namespace] = records
            existing_entities.extend(self.entity_database_store(namespace).all_records())

        total = sum(len(records) for records in records_by_namespace.values())
        if not total:
            return 0

        def prepare_normalized_records(set_progress, is_cancelled):
            normalized_by_namespace = {}
            processed = 0
            for namespace, records in records_by_namespace.items():
                if is_cancelled():
                    return None
                namespace_start = processed
                normalized = normalize_entity_references(
                    records,
                    existing_entities,
                    source_namespace=namespace,
                    is_cancelled=is_cancelled,
                    progress_callback=lambda namespace_current, namespace_total: set_progress(
                        namespace_start + namespace_current,
                        total,
                    ),
                )
                if len(normalized) != len(records):
                    return None
                normalized_by_namespace[namespace] = normalized
                processed += len(normalized)
            return normalized_by_namespace

        progress_dialog = progress_factory(
            self.task_runner,
            prepare_normalized_records,
            "stored entity references",
            operation_name="Normalising references...",
            parent=parent,
        )
        if progress_dialog.exec() != QDialog.DialogCode.Accepted:
            return 0
        normalized_by_namespace = progress_dialog.model.result
        if normalized_by_namespace is None:
            return 0

        updated = 0
        for namespace, normalized in normalized_by_namespace.items():
            store = self.entity_database_store(namespace)
            store.commit_records(normalized, duplicate_policy="replace")
            updated += len(normalized)
            self.save_entity_namespace_json(namespace)
        if updated and self.project_file is not None:
            self.save_project()
        return updated

    def resolve_unresolved_reference(
        self, entity_type, display_fallback, target_uid
    ):
        """Resolve every matching unresolved reference to one canonical entity."""
        from application.entity_references import _link_display_name, _reference_key
        from application.imports import ImportedEntityRecord

        target = self.resolve_entity(target_uid)
        target_reference = {
            "target_uid": target.uid,
            "entity_type": target.entity_type,
            "source_namespace": target.source_namespace,
        }
        target_key = (entity_type, _reference_key(display_fallback))
        updated_uids = []
        for namespace in ("compendium", "homebrew"):
            block_uid = f"dmtools-{namespace}-entity-database"
            if not self.project.blocks.contains(block_uid):
                continue
            store = self.entity_database_store(namespace)
            replacements = []
            for row in store.all_records():
                metadata = dict(row.source_metadata)
                diagnostics = metadata.get("reference_diagnostics", ())
                matching = [
                    diagnostic
                    for diagnostic in diagnostics
                    if (
                        diagnostic.get("entity_type"),
                        _reference_key(diagnostic.get("display_fallback", "")),
                    )
                    == target_key
                ]
                if not matching:
                    continue
                references = list(metadata.get("entity_references", ()))
                for diagnostic in matching:
                    references.append({
                        "path": diagnostic["path"],
                        **target_reference,
                        "display_fallback": _link_display_name(
                            diagnostic["display_fallback"]
                        ),
                    })
                remaining = [
                    diagnostic
                    for diagnostic in diagnostics
                    if diagnostic not in matching
                ]
                metadata["entity_references"] = references
                if remaining:
                    metadata["reference_diagnostics"] = remaining
                else:
                    metadata.pop("reference_diagnostics", None)
                replacements.append(
                    ImportedEntityRecord(
                        entity_type=row.entity_type,
                        uid=row.uid,
                        source_identity=row.source_identity,
                        display_name=row.name,
                        payload=row.payload,
                        source_metadata=metadata,
                        provenance=row.provenance,
                    )
                )
            if replacements:
                store.commit_records(replacements, duplicate_policy="replace")
                updated_uids.extend(record.uid for record in replacements)
        if updated_uids and self.project_file is not None:
            self.save_project()
        return tuple(updated_uids)

    def persist_imported_entities(
        self,
        records,
        *,
        namespace="compendium",
        duplicate_policy="replace",
        progress_callback=None,
        database_path=None,
    ):
        """Persist records without touching Project or Qt-owned state."""
        from application.entity_database import EntityDatabaseStore

        if database_path is None:
            database_path = self.entity_database_store(namespace).database_path
        worker_store = EntityDatabaseStore(database_path, namespace=namespace)
        return worker_store.commit_records(
            records,
            duplicate_policy=duplicate_policy,
            progress_callback=progress_callback,
            sync_block_metadata=False,
        )

    def commit_imported_entities(
        self,
        records,
        *,
        namespace="compendium",
        duplicate_policy="replace",
        persist=True,
    ):
        """Atomically persist a validated batch, then register its tree projection."""
        if persist:
            records = self.prepare_imported_entities(records, namespace=namespace)
            self.persist_imported_entities(
                records,
                namespace=namespace,
                duplicate_policy=duplicate_policy,
            )
        root = compendium_root if namespace == "compendium" else homebrew_root
        store = self.entity_database_store(namespace)
        count = store.count()
        for record in records:
            node_uid = f"dmtools-{namespace}-entity-{record.uid}"
            if self.project.nodes.contains(node_uid):
                continue
            from projectfoundry.tree import TreeNode

            node = TreeNode(record.display_name, uid=node_uid)
            node.node_type = "entity"
            node.namespace = namespace
            node.entity_type = record.entity_type
            node.entity_uid = record.uid
            self.project.add_node(
                node,
                parent_uid=root.category(record.entity_type).uid,
            )
        if namespace == "homebrew":
            self._refresh_homebrew_rules()
        self.project_tree_model.refresh()
        return count

    def register_entity_query(self, query_block):
        """Register a validated saved query and its database relationship."""
        from application.entity_queries import EntityQueryFactory

        data = query_block.block_data
        EntityQueryFactory().create(
            query_block.name,
            database_uid=data.database_uid,
            entity_type=data.entity_type,
            field=data.field,
            operator=data.operator,
            value=data.value,
            sort_field=data.sort_field,
            sort_order=data.sort_order,
            projection=data.projection,
            guid=query_block.guid,
        )
        if not self.project.blocks.contains(data.database_uid):
            raise ValueError("Saved query database UID is not in the active project")
        database = self.project.blocks.get(data.database_uid)
        if getattr(database, "type_name", None) != "entity_database":
            raise ValueError("Saved query database UID is not an entity database")
        if getattr(query_block, "_project", None) not in (None, self.project):
            raise ValueError("Saved query belongs to another project")
        self.project.add_block(query_block)
        self.project.connect_blocks(database.guid, query_block.guid)
        self.refresh_project_tree()
        return query_block

    def update_entity_query(self, query_uid, **changes):
        """Validate and apply saved-query metadata through the active project."""
        from application.entity_queries import EntityQueryFactory

        query = self.project.blocks.get(query_uid)
        if getattr(query, "type_name", None) != "entity_saved_query":
            raise ValueError("Expected a saved entity query")
        data = query.block_data
        values = data.model_dump(exclude={"artifact"})
        name = changes.pop("name", query.name)
        values.update(changes)
        candidate = EntityQueryFactory().create(name, guid=query.guid, **values)
        query.name = candidate.name
        query.block_data = candidate.block_data
        query.mark_changed()
        self.refresh_project_tree()
        return query

    def duplicate_entity_query(self, query_uid, name=None):
        """Create an independently identified copy of a saved query."""
        from application.entity_queries import EntityQueryFactory

        source = self.project.blocks.get(query_uid)
        if getattr(source, "type_name", None) != "entity_saved_query":
            raise ValueError("Expected a saved entity query")
        values = source.block_data.model_dump(exclude={"artifact"})
        duplicate = EntityQueryFactory().create(
            name or f"{source.name} Copy",
            **values,
        )
        return self.register_entity_query(duplicate)

    def unregister_entity_query(self, query_uid):
        """Remove a saved query and its projected nodes."""
        query = self.project.blocks.get(query_uid)
        if getattr(query, "type_name", None) != "entity_saved_query":
            raise ValueError("Expected a saved entity query")
        for node in tuple(self.project.nodes.values()):
            if node.object_uid == query_uid:
                self.project.remove_node(node.uid)
        self.project.remove_block(query_uid)
        self.project_tree_model.refresh()

    def execute_entity_query(self, query_uid, limit=100):
        """Resolve a saved query and execute it against its owned database."""
        from application.entity_queries import EntityQueryFactory

        query = self.project.blocks.get(query_uid)
        if getattr(query, "type_name", None) != "entity_saved_query":
            raise ValueError("Expected a saved entity query")
        if not self.project.blocks.contains(query.block_data.database_uid):
            raise ValueError("Saved query database UID is missing from the active project")
        database = self.project.blocks.get(query.block_data.database_uid)
        store = self.entity_database_store(database.block_data.namespace)
        return EntityQueryFactory.execute(store, query, limit=limit)

    def create_collection(
        self,
        name,
        *,
        description="",
        entity_uids=(),
        dynamic_query_uid=None,
    ):
        """Create a collection after validating every active-project reference."""
        from objects.collection import CollectionBlock

        if not name.strip():
            raise ValueError("Collection name is required")
        entity_uids = list(entity_uids)
        if len(entity_uids) != len(set(entity_uids)):
            raise ValueError("Collection cannot contain duplicate entity UIDs")
        for entity_uid in entity_uids:
            self.resolve_entity(entity_uid)
        if dynamic_query_uid is not None:
            query = self.project.blocks.get(dynamic_query_uid)
            if getattr(query, "type_name", None) != "entity_saved_query":
                raise ValueError("Dynamic collection requires a saved entity query")
        collection = CollectionBlock(
            name.strip(),
            description=description.strip(),
            entity_uids=entity_uids,
            dynamic_query_uid=dynamic_query_uid,
        )
        self.project.add_block(collection)
        if dynamic_query_uid is not None:
            self.project.connect_blocks(collection.guid, dynamic_query_uid)
        self.refresh_project_tree()
        return collection

    def update_collection(self, collection_uid, *, name=None, description=None):
        collection = self._collection(collection_uid)
        if name is not None:
            if not name.strip():
                raise ValueError("Collection name is required")
            collection.name = name.strip()
        if description is not None:
            collection.block_data.description = description.strip()
        collection.mark_changed()
        self.refresh_project_tree()
        return collection

    def duplicate_collection(self, collection_uid, name=None):
        collection = self._collection(collection_uid)
        data = collection.block_data
        return self.create_collection(
            name or f"{collection.name} Copy",
            description=data.description,
            entity_uids=data.entity_uids,
            dynamic_query_uid=data.dynamic_query_uid,
        )

    def remove_collection(self, collection_uid):
        self._collection(collection_uid)
        for node in tuple(self.project.nodes.values()):
            if node.object_uid == collection_uid:
                self.project.remove_node(node.uid)
        self.project.remove_block(collection_uid)
        self.project_tree_model.refresh()

    def add_collection_entity(self, collection_uid, entity_uid):
        collection = self._collection(collection_uid)
        self.resolve_entity(entity_uid)
        if entity_uid in collection.block_data.entity_uids:
            raise ValueError("Entity is already in the collection")
        collection.block_data.entity_uids.append(entity_uid)
        collection.mark_changed()
        return collection

    def remove_collection_entity(self, collection_uid, entity_uid):
        collection = self._collection(collection_uid)
        if entity_uid not in collection.block_data.entity_uids:
            return False
        collection.block_data.entity_uids.remove(entity_uid)
        collection.mark_changed()
        return True

    def reorder_collection_entities(self, collection_uid, entity_uids):
        """Replace only membership order, never membership identity."""
        collection = self._collection(collection_uid)
        entity_uids = list(entity_uids)
        if len(entity_uids) != len(set(entity_uids)):
            raise ValueError("Collection order cannot contain duplicate entity UIDs")
        if set(entity_uids) != set(collection.block_data.entity_uids):
            raise ValueError("Collection reorder must preserve every member UID")
        collection.block_data.entity_uids = entity_uids
        collection.mark_changed()
        return collection

    def capture_query_results(self, collection_uid, query_uid):
        collection = self._collection(collection_uid)
        for row in self.execute_entity_query(query_uid, limit=1000):
            if row.uid not in collection.block_data.entity_uids:
                collection.block_data.entity_uids.append(row.uid)
        collection.mark_changed()
        return collection

    def resolve_collection_members(self, collection_uid, include_dynamic=True):
        from application.entity_database import MissingEntityRow

        collection = self._collection(collection_uid)
        uids = list(collection.block_data.entity_uids)
        query_uid = collection.block_data.dynamic_query_uid
        if include_dynamic and query_uid is not None:
            for row in self.execute_entity_query(query_uid, limit=1000):
                if row.uid not in uids:
                    uids.append(row.uid)
        results = []
        for entity_uid in uids:
            try:
                results.append(self.resolve_entity(entity_uid))
            except ValueError:
                results.append(MissingEntityRow(entity_uid))
        return tuple(results)

    def search_collection(self, collection_uid, text="", entity_type=None):
        """Filter collection members while retaining canonical source metadata."""
        query = str(text).strip().casefold()
        results = []
        for entity in self.resolve_collection_members(collection_uid):
            if getattr(entity, "missing", False):
                continue
            if entity_type is not None and entity.entity_type != entity_type:
                continue
            searchable = " ".join(
                (entity.name, entity.entity_type, entity.source_namespace)
            ).casefold()
            if query and query not in searchable:
                continue
            results.append(entity)
        return tuple(results)

    def resolve_entity(self, entity_uid):
        for namespace in ("compendium", "homebrew"):
            block_uid = f"dmtools-{namespace}-entity-database"
            if not self.project.blocks.contains(block_uid):
                continue
            row = self.entity_database_store(namespace).get(entity_uid)
            if row is not None:
                return row
        raise ValueError(f"Unknown active-project entity UID: {entity_uid}")

    def resolve_entity_reference(self, reference):
        """Resolve and validate one canonical entity reference."""
        if reference.source_namespace == "collection":
            collection = self._collection(reference.target_uid)
            if reference.entity_type != "collection":
                raise ValueError("Collection reference has an incompatible entity type")
            return collection
        entity = self.resolve_entity(reference.target_uid)
        if entity.source_namespace != reference.source_namespace:
            raise ValueError("Entity reference source namespace does not match its target")
        if entity.entity_type != reference.entity_type:
            raise ValueError("Entity reference type does not match its target")
        return entity

    def create_homebrew_entity(self, draft):
        """Validate and commit one accepted Homebrew draft."""
        record = draft.apply()
        self.commit_imported_entities((record,), namespace="homebrew")
        return self.resolve_entity(record.uid)

    def update_homebrew_entity(self, entity_uid, draft):
        """Validate a draft before replacing one canonical Homebrew row."""
        current = self.resolve_entity(entity_uid)
        if current.source_namespace != "homebrew":
            raise ValueError("Only Homebrew entities can be edited")
        if draft.entity_type != current.entity_type:
            raise ValueError("A Homebrew entity type cannot be changed during edit")
        draft.entity_uid = current.uid
        draft.source_identity = current.source_identity
        record = draft.apply()
        self.commit_imported_entities(
            (record,), namespace="homebrew", duplicate_policy="replace"
        )
        node = self.project.nodes.get(f"dmtools-homebrew-entity-{entity_uid}")
        node.name = record.display_name
        self.project_tree_model.refresh()
        return self.resolve_entity(entity_uid)

    def duplicate_homebrew_entity(self, entity_uid, name=None):
        """Create an independently identified Homebrew copy."""
        from application.homebrew import HomebrewDraft

        source = self.resolve_entity(entity_uid)
        if source.source_namespace != "homebrew":
            raise ValueError("Only Homebrew entities can be duplicated")
        draft = HomebrewDraft.from_entity(source)
        draft.name = name or f"{source.name} Copy"
        return self.create_homebrew_entity(draft)

    def delete_homebrew_entity(self, entity_uid):
        """Remove one Homebrew entity and its tree projection."""
        entity = self.resolve_entity(entity_uid)
        if entity.source_namespace != "homebrew":
            raise ValueError("Only Homebrew entities can be deleted")
        node_uid = f"dmtools-homebrew-entity-{entity_uid}"
        if not self.project.nodes.contains(node_uid):
            raise ValueError("Homebrew entity has no active-project tree node")
        self.entity_database_store("homebrew").delete(entity_uid)
        self.project.remove_node(node_uid)
        self.project_tree_model.refresh()

    def copy_entity_to_homebrew(self, entity_uid):
        """Create a new Homebrew record linked to, but separate from, its source."""
        from application.homebrew import HomebrewDraft

        source = self.resolve_entity(entity_uid)
        if source.source_namespace != "compendium":
            raise ValueError("Only Compendium entities can be copied to Homebrew")
        return self.create_homebrew_entity(HomebrewDraft.from_entity(source))

    def _collection(self, collection_uid):
        collection = self.project.blocks.get(collection_uid)
        if getattr(collection, "type_name", None) != "collection":
            raise ValueError("Expected a collection block")
        return collection

    def register_table(self, table_object, parent=None):
        """Add a table and its disk-backed block through the active project."""
        block = table_object.block_object
        if getattr(block, "_project", None) not in (None, self.project):
            raise ValueError("Table belongs to another project")
        table_object.add_to_tree(self.tree_manager, parent)
        self.refresh_project_tree()
        return table_object

    def register_shopkeeper(self, shopkeeper, parent=None):
        """Validate and register Shopkeeper UID relationships atomically."""
        block = shopkeeper.block_object
        data = block.block_data
        if getattr(block, "_project", None) not in (None, self.project):
            raise ValueError("Shopkeeper belongs to another project")
        if data.database_uid is not None:
            if not self.project.blocks.contains(data.database_uid):
                raise ValueError("Shopkeeper database UID is not in the active project")
            database = self.project.blocks.get(data.database_uid)
            if getattr(database, "type_name", None) not in {
                "database",
                "entity_database",
            }:
                raise ValueError("Shopkeeper database UID is not a database")
        for query_uid in data.query_uids:
            if not self.project.blocks.contains(query_uid):
                raise ValueError(f"Shopkeeper query UID is missing: {query_uid}")
            if getattr(self.project.blocks.get(query_uid), "type_name", None) not in {
                "query",
                "entity_saved_query",
            }:
                raise ValueError(f"Shopkeeper query UID is not a query: {query_uid}")
        shopkeeper.add_to_tree(self.tree_manager, parent)
        self.refresh_project_tree()
        if data.database_uid is not None:
            self.project.connect_blocks(data.database_uid, block.guid)
        return shopkeeper

    def unregister_shopkeeper(self, shopkeeper_uid):
        """Remove a registered Shopkeeper block and its projected node."""
        block = self.project.blocks.get(shopkeeper_uid)
        if getattr(block, "type_name", None) != "shopkeeper":
            raise ValueError("Expected a Shopkeeper block")
        for node in tuple(self.project.nodes.values()):
            if node.object_uid == shopkeeper_uid:
                self.project.remove_node(node.uid)
        self.project.remove_block(shopkeeper_uid)
        self.project_tree_model.refresh()

    def commit_table(self, table_object):
        """Atomically persist a registered table's DataFrame artifact."""
        block = self.project.resolve_block(table_object.guid)
        if block is not table_object.block_object:
            raise ValueError("Table block is not registered with the active project")
        if self.project.artifact_store is None:
            raise RuntimeError("Project has no artifact store")
        block.commit(table_object.data, self.project.artifact_store)
        table_object.release_data()
        return block.block_data.artifact

    def load_table_data(self, table_uid):
        """Lazily load a registered table artifact through the active project."""
        block = self.project.resolve_block(table_uid)
        from objects.table_object import TableBlock

        if not isinstance(block, TableBlock):
            raise TypeError(f"Block is not a table: {table_uid}")
        return self.project.load_block_artifact(table_uid, block.load_artifact)

    def register_database(self, database_object):
        """Register a DMTools database block in the active project."""
        block = database_object.block_object
        if getattr(block, "_project", None) not in (None, self.project):
            raise ValueError("Database belongs to another project")
        self.project.add_block(block)
        database_object._project_controller = self
        self.refresh_project_tree()
        return database_object

    def unregister_database(self, database_object):
        """Remove a database block from the active project if present."""
        self.refresh_project_tree()
        if self.project.blocks.contains(database_object.guid):
            self.project.remove_block(database_object.guid)
        database_object._project_controller = None

    def register_query(self, database_object, query_object):
        """Attach and register a saved query through the active project."""
        database_object.add_query_object(query_object)
        self.refresh_project_tree()
        return query_object

    def unregister_query(self, database_object, query_object):
        """Remove a saved query relationship from the active project."""
        database_object.query_objects = [
            query for query in database_object.query_objects if query is not query_object
        ]
        query_object.remove_from_tree()
        database_object._changed()
        self.refresh_project_tree()
        if self.project.blocks.contains(query_object.guid):
            self.project.remove_block(query_object.guid)

    def update_query(
        self,
        database_object,
        query_object,
        *,
        sql,
        table_name,
        filters,
        lookup,
        name=None,
    ):
        """Apply validated query editor state to a registered query."""
        if name is not None:
            query_object._on_name_changed(name)
            query_object.block_object.name = name
        query_object.sql = sql
        query_object.table_name = table_name
        query_object.filters = list(filters)
        query_object.lookup = lookup
        query_object.block_object.block_data.sql = sql
        query_object.block_object.block_data.table_name = table_name
        query_object.block_object.block_data.filters = [
            condition if isinstance(condition, dict) else condition.__dict__
            for condition in query_object.filters
        ]
        query_object.block_object.block_data.lookup = (
            lookup if isinstance(lookup, dict) else lookup.__dict__
        )
        query_object.block_object.mark_changed()
        database_object._changed()
        self.refresh_project_tree()
        return query_object

    def refresh_project_tree(self):
        self._refresh_homebrew_rules()
        project_roots = self.tree_projection.refresh()
        self._migrate_subclass_nodes()
        self.project_tree_model.root_data = [
            node
            for node in project_roots
            if node.uid != database_root.uid
        ]
        self.project_tree_model.refresh()

    def _refresh_homebrew_rules(self):
        block_uid = "dmtools-homebrew-entity-database"
        if not self.project.blocks.contains(block_uid):
            homebrew_root.rules.set_custom_values(())
            return
        values = []
        for record in self.entity_database_store("homebrew").all_records():
            values.extend(custom_rule_values(record.entity_type, record.payload))
        homebrew_root.rules.set_custom_values(values)

    def _migrate_subclass_nodes(self):
        for node in tuple(self.project.nodes.values()):
            if (
                getattr(node, "node_type", None) != "entity"
                or getattr(node, "entity_type", None) != "subclass"
            ):
                continue
            namespace = getattr(node, "namespace", None)
            expected_parent_uid = f"dmtools-{namespace}-subclass-category"
            if node.parent_uid == expected_parent_uid:
                continue
            if not self.project.nodes.contains(expected_parent_uid):
                continue
            object_uid = getattr(node, "object_uid", None)
            self.project.remove_node(node.uid)
            self.project.add_node(
                node,
                object_uid=object_uid,
                parent_uid=expected_parent_uid,
            )

    def _resolve_duplicate_name(self, name, object_base):
        next_name = self.tree_model.next_name(name, exclude=object_base)
        if self._duplicate_name_dialog is None:
            return next_name
        dialog = self._duplicate_name_dialog(name, next_name)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None
        return next_name

    def _rename_tree_object(self, object_base, name):
        """Apply a tree rename through the active Project when registered."""
        block = getattr(object_base, "block_object", None)
        if block is not None and self.project.blocks.contains(block.guid):
            self.tree_mutations.rename_block(block.guid, name)
        object_base._on_name_changed(name)
        return True

    def new_project(self):
        """Reset to an empty, unsaved project."""
        self._notify_project_replacement()
        self._close_active_project()
        self.project = self.lifecycle_service.new_project(self._artifact_store)
        self.task_runner.runner.project = self.project
        self.project_service = ProjectService(
            self.project, task_runner=self.task_runner
        )
        self.tree_mutations = ProjectTreeMutationService(self.project)
        self.tree_projection = LegacyTreeProjectionAdapter(self.project)
        self.project_context = None
        root_objects.reset()
        self.tree_manager.root_nodes = root_objects.get_nodes()
        self.tree_model.root_data = self.tree_manager.root_nodes
        self.tree_model.refresh()
        self.refresh_project_tree()
        self.project_file = None

    def close(self):
        """Release ProjectFoundry-owned runtime resources."""
        self.task_runner.shutdown()
        self._close_active_project()

    def _close_active_project(self):
        if self.project_context is not None:
            self.project_context.close()
            self.project_context = None
        else:
            self.project.shutdown()

    def create_project(self, project_directory):
        """Create and save a new project directory."""
        self.new_project()
        (
            self.project_file,
            self.project_context,
            self._artifact_store,
        ) = self.lifecycle_service.create(
            project_directory,
            self.project,
            self.tree_manager,
        )
        return self.project_file

    def save_project(self, parent=None):
        """Save the current project to its active project file."""
        if self.project_file is None:
            return self.save_project_as(parent)
        saved = self.lifecycle_service.save(
            self.project_file, self.project, self.tree_manager
        )
        if self.project_context is not None:
            self.project_context.dirty = False
        return saved

    def save_project_as(self, parent=None):
        """Save the current project to a newly selected project file."""
        project_file, _ = QFileDialog.getSaveFileName(
            parent,
            "Save Project As",
            filter="Project files (project.json);;JSON files (*.json)",
        )
        if not project_file:
            return None
        saved_file = self.lifecycle_service.save(
            project_file, self.project, self.tree_manager
        )
        self.project_file = saved_file
        if self.project_context is None:
            self.project_context = ProjectContext(saved_file, saved_file.parent, self.project)
        else:
            self.project_context.package_path = saved_file
            self.project_context.working_directory = saved_file.parent
            self.project_context.dirty = False
        return saved_file

    def open_project(self, parent=None):
        """Ask the user for a project file, then load it."""
        project_file, _ = QFileDialog.getOpenFileName(
            parent,
            "Open Project",
            filter="Project files (project.json);;JSON files (*.json)",
        )
        if not project_file:
            return None
        return self.load_project(project_file)

    def load_project(self, project_file):
        """Load a project and make its file the active save target."""
        project_file = Path(project_file)
        loaded_project = self.lifecycle_service.load(
            project_file, self.tree_manager, self.tree_model
        )
        return self._replace_loaded_project(project_file, loaded_project)

    def import_legacy_project(self, project_file):
        """Explicitly import a roots-only legacy DMTools project."""
        project_file = Path(project_file)
        loaded_project = self.lifecycle_service.import_legacy(
            project_file, self.tree_manager, self.tree_model
        )
        return self._replace_loaded_project(project_file, loaded_project)

    def _replace_loaded_project(self, project_file, loaded_project):
        self._notify_project_replacement()
        candidate = loaded_project.project
        loaded = loaded_project.loaded_objects
        previous = self.project
        previous_context = self.project_context
        self._artifact_store = loaded_project.artifact_store
        self.project = candidate
        self.task_runner.runner.project = candidate
        self.project_service = ProjectService(
            candidate, task_runner=self.task_runner
        )
        self.tree_mutations = ProjectTreeMutationService(candidate)
        self.project_context = loaded_project.context
        self.project_tree_manager = candidate.tree
        self.tree_projection = LegacyTreeProjectionAdapter(candidate)
        self.refresh_project_tree()
        if previous_context is not None:
            previous_context.close()
        else:
            previous.shutdown()
        self.project_file = project_file
        return loaded
