from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QVBoxLayout,
)

from components.tree.roots.entity_roots import ENTITY_CATEGORIES


class PurgeDataView(QDialog):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.setWindowTitle("Purge Entity Data")
        self.namespace = QComboBox(self)
        self.namespace.addItem("Compendium", "compendium")
        self.namespace.addItem("Homebrew", "homebrew")
        self.namespace.setCurrentIndex(self.namespace.findData(model.namespace))
        self.checkboxes = {}
        for entity_type, label in ENTITY_CATEGORIES:
            checkbox = QCheckBox(label, self)
            checkbox.setChecked(entity_type in model.entity_types)
            self.checkboxes[entity_type] = checkbox
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel,
            parent=self,
        )
        buttons.accepted.connect(self._accept)
        buttons.rejected.connect(self.reject)
        form = QFormLayout()
        form.addRow("Namespace", self.namespace)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        for checkbox in self.checkboxes.values():
            layout.addWidget(checkbox)
        layout.addWidget(buttons)

    def _accept(self):
        self.model.set_namespace(self.namespace.currentData())
        self.model.set_entity_types(
            entity_type
            for entity_type, checkbox in self.checkboxes.items()
            if checkbox.isChecked()
        )
        try:
            self.model.validate()
        except ValueError as error:
            self.setWindowTitle(str(error))
            return
        self.accept()