"""ProjectFoundry tree projection for the transitional DMTools tree."""

from projectfoundry.tree import TreeNode

from components.tree.roots.db_root import database_root
from components.tree.roots.entity_roots import category_entity_type


class ProjectTreeMutationService:
    """Validate and apply supported tree mutations through a Project."""

    def __init__(self, project):
        self.project = project

    def create_block(self, block, *, parent_uid, node_uid=None):
        if self.project.blocks.contains(block.guid):
            raise ValueError(f"Block UID already exists: {block.guid}")
        if not self.project.nodes.contains(parent_uid):
            raise ValueError(f"Parent node UID is missing: {parent_uid}")
        node_uid = node_uid or f"{block.guid}-node"
        if self.project.nodes.contains(node_uid):
            raise ValueError(f"Node UID already exists: {node_uid}")

        node = TreeNode(block.name, uid=node_uid)
        try:
            self.project.add_block(block)
            self.project.add_node(node, object_uid=block.guid, parent_uid=parent_uid)
        except Exception:
            if self.project.nodes.contains(node_uid):
                self.project.remove_node(node_uid)
            if self.project.blocks.contains(block.guid):
                self.project.remove_block(block.guid)
            raise
        return node

    def rename_block(self, block_uid, name):
        name = str(name).strip()
        if not name:
            raise ValueError("Block name is required")
        if not self.project.blocks.contains(block_uid):
            raise ValueError(f"Block UID is missing: {block_uid}")
        self.project.rename_block(block_uid, name)
        return self.project.blocks.get(block_uid)

    def delete_block(self, block_uid):
        if not self.project.blocks.contains(block_uid):
            raise ValueError(f"Block UID is missing: {block_uid}")
        node_uids = tuple(
            node.guid
            for node in self.project.nodes.values()
            if node.object_uid == block_uid
        )
        for node_uid in node_uids:
            self.project.remove_node(node_uid)
        return self.project.remove_block(block_uid)


class ProtectedTreeNode(TreeNode):
    """Projected structural node that cannot be removed by tree commands."""

    protected = True

    def can_delete(self):
        return False

    def delete(self):
        return False


def rebuild_project_tree(project, legacy_roots):
    """Incrementally synchronize compatibility nodes into the canonical tree."""
    registered_blocks = {block.guid for block in project.blocks.values()}

    def ensure_node(legacy_node, *, object_uid=None, parent_uid=None):
        if project.nodes.contains(legacy_node.uid):
            node = project.nodes.get(legacy_node.uid)
            if node.parent_uid != parent_uid:
                raise ValueError(
                    f"Cannot implicitly move project node {legacy_node.uid}"
                )
            node.name = legacy_node.name
            node.node_object = legacy_node.node_object
            node.object_uid = object_uid
        else:
            node_class = (
                ProtectedTreeNode
                if getattr(legacy_node, "protected", False)
                else TreeNode
            )
            node = node_class(
                legacy_node.name,
                node_object=legacy_node.node_object,
                uid=legacy_node.uid,
            )
            project.add_node(node, object_uid=object_uid, parent_uid=parent_uid)
        for field in (
            "node_type",
            "namespace",
            "entity_type",
            "category_type",
            "value",
            "schema_names",
            "protected",
        ):
            value = getattr(legacy_node, field, None)
            if value is not None:
                setattr(node, field, value)
        return node

    def mirror(legacy_node, parent_uid=None, parent_block_uid=None):
        block = getattr(legacy_node.node_object, "block_object", None)
        if block is not None and getattr(block, "_project", None) not in (None, project):
            block = None
        if block is not None and block.guid not in registered_blocks:
            project.add_block(block)
            registered_blocks.add(block.guid)
        if block is not None and parent_block_uid is not None:
            project.connect_blocks(parent_block_uid, block.guid)
        node = ensure_node(
            legacy_node,
            object_uid=block.guid if block is not None else None,
            parent_uid=parent_uid,
        )
        for child in legacy_node.children:
            mirror(child, node.guid, block.guid if block is not None else parent_block_uid)
        return node

    roots = tuple(mirror(root) for root in legacy_roots)
    for block in project.blocks.values():
        block_type = getattr(block, "type_name", None)
        if block_type == "entity_database":
            node_uid = f"{block.guid}-node"
            if project.nodes.contains(node_uid):
                project.remove_node(node_uid)
            continue
        if block_type == "entity_saved_query":
            database = project.blocks.get(block.block_data.database_uid)
            namespace = database.block_data.namespace
            category_type = category_entity_type(block.block_data.entity_type)
            parent_uid = f"dmtools-{namespace}-{category_type}-category"
        elif block_type == "collection":
            parent_uid = "dmtools-collections-root"
        elif block_type == "shopkeeper":
            database_uid = block.block_data.database_uid
            database_node_uid = f"{database_uid}-node"
            parent_uid = (
                database_node_uid
                if database_uid and project.nodes.contains(database_node_uid)
                else database_root.uid
            )
        else:
            continue
        node_uid = f"{block.guid}-node"
        if project.nodes.contains(node_uid):
            node = project.nodes.get(node_uid)
            node.name = block.name
            node.object_uid = block.guid
        else:
            project.add_node(
                TreeNode(block.name, uid=node_uid),
                object_uid=block.guid,
                parent_uid=parent_uid,
            )
    return roots