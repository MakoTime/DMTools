from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSpinBox, QWidget


class PaginationControls(QWidget):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.model = model
        self.previous_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.page_spin = QSpinBox()
        self.page_label = QLabel()
        self.page_spin.setMinimum(1)
        self.previous_button.clicked.connect(lambda: self._set_page(model.page - 1))
        self.next_button.clicked.connect(lambda: self._set_page(model.page + 1))
        self.page_spin.valueChanged.connect(lambda value: self._set_page(value - 1))
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.next_button)
        layout.addWidget(QLabel("Page"))
        layout.addWidget(self.page_spin)
        layout.addWidget(self.page_label)
        self.refresh()

    def refresh(self):
        self.page_spin.blockSignals(True)
        self.page_spin.setMaximum(self.model.page_count)
        self.page_spin.setValue(self.model.page + 1)
        self.page_spin.blockSignals(False)
        self.previous_button.setEnabled(self.model.page > 0)
        self.next_button.setEnabled(self.model.page < self.model.page_count - 1)
        self.page_label.setText(f"of {self.model.page_count}")

    def set_model(self, model):
        self.model = model
        self.refresh()

    def _set_page(self, page):
        self.model.set_page(page)
        self.refresh()
