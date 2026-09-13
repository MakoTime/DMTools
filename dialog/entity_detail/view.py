from PySide6.QtWidgets import (
    QDialogButtonBox,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
)

from dialog.base.popup_editor import PopupEditorView

from .model import EntityDetailModel


class EntityDetailView(PopupEditorView):
    """Display a canonical entity and its structured schema data."""

    def __init__(
        self,
        model: EntityDetailModel,
        parent=None,
        *,
        project_controller=None,
        on_clone=None,
        on_edit=None,
    ):
        super().__init__(model, parent=parent)
        self.setWindowTitle(model.title)
        self.resize(720, 620)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(("Field", "Value"))
        self.tree.header().setStretchLastSection(True)
        for name, value in model.details.items():
            self._add_value(self.tree.invisibleRootItem(), name, value)
        self.tree.expandToDepth(1)

        buttons = self.create_button_box(QDialogButtonBox.StandardButton.Close)
        if (
            project_controller is not None
            and model.entity.source_namespace == "compendium"
        ):
            clone_button = QPushButton("Clone to Homebrew", self)
            clone_button.clicked.connect(
                lambda: self._clone_to_homebrew(project_controller, on_clone)
            )
            buttons.addButton(clone_button, QDialogButtonBox.ButtonRole.ActionRole)
        if project_controller is not None and model.entity.source_namespace == "homebrew":
            edit_button = QPushButton("Edit Homebrew", self)
            edit_button.clicked.connect(
                lambda: on_edit(model.entity) if on_edit is not None else None
            )
            buttons.addButton(edit_button, QDialogButtonBox.ButtonRole.ActionRole)
        layout = QVBoxLayout(self)
        layout.addWidget(self.tree, 1)
        layout.addWidget(buttons)

    def _clone_to_homebrew(self, project_controller, on_clone):
        clone = project_controller.copy_entity_to_homebrew(self.model.entity.uid)
        if on_clone is not None:
            on_clone(clone)
        return clone

    def _add_value(self, parent, name, value):
        if isinstance(value, dict):
            item = QTreeWidgetItem(parent, (str(name), ""))
            for child_name, child_value in value.items():
                self._add_value(item, child_name.replace("_", " ").title(), child_value)
            return
        if isinstance(value, list):
            item = QTreeWidgetItem(parent, (str(name), f"{len(value)} item(s)"))
            for index, child_value in enumerate(value, start=1):
                self._add_value(item, str(index), child_value)
            return
        QTreeWidgetItem(parent, (str(name), "" if value is None else str(value)))
