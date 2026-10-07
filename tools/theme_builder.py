"""Visual controls that edit the same QSS source shown in the text editor."""

from __future__ import annotations

import re
from uuid import uuid4

from PySide6.QtCore import QSignalBlocker, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFontComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QPlainTextEdit,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


FEATURE_OPTIONS = (
    ("App windows", "QDialog"),
    ("Content surfaces", "QWidget"),
    ("Headings and labels", "QLabel"),
    ("Buttons", "QPushButton"),
    ("Text fields", "QLineEdit"),
    ("Dropdowns", "QComboBox"),
    ("Check boxes", "QCheckBox"),
    ("Radio buttons", "QRadioButton"),
    ("Group boxes", "QGroupBox"),
    ("Tab panels", "QTabWidget::pane"),
    ("Selected tab", "QTabBar::tab:selected"),
    ("Tables", "QTableWidget"),
    ("Sliders", "QSlider::handle:horizontal"),
    ("Progress bars", "QProgressBar"),
)

PROPERTY_OPTIONS = (
    ("Text color", "color"),
    ("Background color", "background-color"),
    ("Border color", "border-color"),
    ("Font family", "font-family"),
    ("Font size", "font-size"),
    ("Font weight", "font-weight"),
    ("Border", "border"),
    ("Border style", "border-style"),
    ("Corner radius", "border-radius"),
    ("Padding", "padding"),
    ("Margin", "margin"),
    ("Minimum width", "min-width"),
    ("Minimum height", "min-height"),
    ("Text alignment", "text-align"),
)

PROPERTY_LABELS = dict((name, label) for label, name in PROPERTY_OPTIONS)
DEFAULT_VALUES = {
    "color": "#292b27",
    "background-color": "#fffdf7",
    "border-color": "#c9c1b0",
    "font-family": "Segoe UI",
    "font-size": "10pt",
    "font-weight": "normal",
    "border": "1px solid #c9c1b0",
    "border-style": "solid",
    "border-radius": "3px",
    "padding": "6px",
    "margin": "0px",
    "min-width": "0px",
    "min-height": "0px",
    "text-align": "left",
}
COLOR_PROPERTIES = {"color", "background-color", "border-color"}
NUMERIC_PROPERTIES = {"border-radius", "padding", "margin", "min-width", "min-height"}
FEATURE_MARKER = "UI VIEWER FEATURE"


class ThemeBuilderPanel(QWidget):
    """Offer a visual rule builder over an editable, authoritative QSS document."""

    stylesheetChanged = Signal(str)

    def __init__(self, stylesheet: str, parent=None):
        super().__init__(parent)
        self.features: list[dict] = []
        self._setting_source = False
        self._build_interface()
        self.set_stylesheet(stylesheet, emit=False)

    @property
    def stylesheet(self) -> str:
        return self.raw_editor.toPlainText()

    def _build_interface(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        features_tab = QWidget()
        features_layout = QVBoxLayout(features_tab)
        features_layout.setContentsMargins(8, 10, 8, 8)
        feature_header = QHBoxLayout()
        feature_heading = QLabel("Custom features")
        feature_heading.setObjectName("uiSectionLabel")
        feature_header.addWidget(feature_heading)
        feature_header.addStretch(1)
        self.add_feature_button = QPushButton("Add feature")
        self.add_feature_button.clicked.connect(self._show_feature_menu)
        feature_header.addWidget(self.add_feature_button)
        features_layout.addLayout(feature_header)

        self.feature_scroll = QScrollArea()
        self.feature_scroll.setWidgetResizable(True)
        self.feature_host = QWidget()
        self.feature_layout = QVBoxLayout(self.feature_host)
        self.feature_layout.setContentsMargins(2, 4, 2, 4)
        self.feature_layout.setSpacing(8)
        self.feature_scroll.setWidget(self.feature_host)
        features_layout.addWidget(self.feature_scroll, 1)
        self.tabs.addTab(features_tab, "Features")

        qss_tab = QWidget()
        qss_layout = QVBoxLayout(qss_tab)
        qss_layout.setContentsMargins(8, 10, 8, 8)
        qss_heading = QLabel("QSS source")
        qss_heading.setObjectName("uiSectionLabel")
        qss_layout.addWidget(qss_heading)
        self.raw_editor = QPlainTextEdit()
        self.raw_editor.setObjectName("themeRawEditor")
        self.raw_editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.raw_editor.setFont(
            QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        )
        self.raw_editor.textChanged.connect(self._on_source_edited)
        qss_layout.addWidget(self.raw_editor, 1)
        self.tabs.addTab(qss_tab, "QSS")
        self._render_features()

    def set_stylesheet(self, stylesheet: str, emit: bool = True) -> None:
        self._setting_source = True
        blocker = QSignalBlocker(self.raw_editor)
        self.raw_editor.setPlainText(stylesheet)
        del blocker
        self._setting_source = False
        self._read_features(stylesheet)
        self._render_features()
        if emit:
            self.stylesheetChanged.emit(self.stylesheet)

    def _on_source_edited(self) -> None:
        if self._setting_source:
            return
        self._read_features(self.stylesheet)
        self._render_features()
        self.stylesheetChanged.emit(self.stylesheet)

    def _read_features(self, stylesheet: str) -> None:
        self.features = []
        marker_pattern = re.compile(
            rf"/\* {FEATURE_MARKER} START ([a-f0-9]+) \*/(.*?)/\* {FEATURE_MARKER} END \1 \*/",
            re.DOTALL,
        )
        for match in marker_pattern.finditer(stylesheet):
            feature_id, content = match.groups()
            rule_match = re.search(r"([^{}]+)\{([^{}]*)\}", content, re.DOTALL)
            selector = rule_match.group(1).strip() if rule_match else ""
            parameters = []
            if rule_match:
                for declaration in rule_match.group(2).split(";"):
                    if ":" not in declaration:
                        continue
                    name, value = declaration.split(":", 1)
                    if name.strip() and value.strip():
                        parameters.append(
                            {"name": name.strip(), "value": value.strip()}
                        )
            feature_option = next(
                ((label, value) for label, value in FEATURE_OPTIONS if value == selector),
                None,
            )
            self.features.append(
                {
                    "id": feature_id,
                    "label": feature_option[0] if feature_option else "Custom selector",
                    "selector": selector,
                    "custom": feature_option is None,
                    "parameters": parameters,
                }
            )

    def _show_feature_menu(self) -> None:
        menu = QMenu(self)
        for label, selector in FEATURE_OPTIONS:
            action = menu.addAction(label)
            action.triggered.connect(
                lambda _checked=False, label=label, selector=selector: self._create_feature(
                    label, selector
                )
            )
        menu.addSeparator()
        action = menu.addAction("Something else...")
        action.triggered.connect(self._create_custom_feature)
        menu.exec(self.add_feature_button.mapToGlobal(self.add_feature_button.rect().bottomLeft()))

    def _create_feature(self, label: str, selector: str) -> None:
        feature = {
            "id": uuid4().hex,
            "label": label,
            "selector": selector,
            "custom": False,
            "parameters": [],
        }
        self.features.append(feature)
        self._write_feature(feature)
        self._render_features()

    def _create_custom_feature(self) -> None:
        feature = {
            "id": uuid4().hex,
            "label": "Something else...",
            "selector": "",
            "custom": True,
            "parameters": [],
        }
        self.features.append(feature)
        self._write_feature(feature)
        self._render_features()

    def _render_features(self) -> None:
        while self.feature_layout.count():
            item = self.feature_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not self.features:
            empty_state = QLabel("No features added")
            empty_state.setObjectName("themeEmptyState")
            empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.feature_layout.addWidget(empty_state)
        else:
            for feature in self.features:
                self.feature_layout.addWidget(self._feature_card(feature))
        self.feature_layout.addStretch(1)

    def _feature_card(self, feature: dict) -> QFrame:
        card = QFrame()
        card.setObjectName("themeFeatureCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(9, 9, 9, 9)
        card_layout.setSpacing(7)

        header = QHBoxLayout()
        feature_picker = QComboBox()
        for label, selector in FEATURE_OPTIONS:
            feature_picker.addItem(label, selector)
        feature_picker.addItem("Something else...", "__custom__")
        if feature["custom"]:
            feature_picker.setCurrentIndex(feature_picker.count() - 1)
        else:
            feature_picker.setCurrentIndex(feature_picker.findData(feature["selector"]))
        header.addWidget(feature_picker, 1)
        remove_feature = QPushButton("Remove")
        remove_feature.clicked.connect(lambda: self._remove_feature(feature))
        header.addWidget(remove_feature)
        card_layout.addLayout(header)

        selector_row = QWidget()
        selector_layout = QHBoxLayout(selector_row)
        selector_layout.setContentsMargins(0, 0, 0, 0)
        selector_layout.addWidget(QLabel("Target"))
        selector_edit = QLineEdit(feature["selector"] if feature["custom"] else "")
        selector_edit.setPlaceholderText("For example: QDialog#SettingsDialog")
        selector_layout.addWidget(selector_edit, 1)
        selector_row.setVisible(feature["custom"])
        card_layout.addWidget(selector_row)

        feature_picker.currentIndexChanged.connect(
            lambda index: self._change_feature_type(
                feature, feature_picker, selector_row, selector_edit, index
            )
        )
        selector_edit.textChanged.connect(
            lambda selector: self._set_custom_selector(feature, selector)
        )

        for parameter in feature["parameters"]:
            card_layout.addWidget(self._parameter_row(feature, parameter))

        setting_picker = QComboBox()
        setting_picker.addItem("Add setting...", "")
        existing = {item["name"] for item in feature["parameters"]}
        for label, property_name in PROPERTY_OPTIONS:
            if property_name not in existing:
                setting_picker.addItem(label, property_name)
        setting_picker.currentIndexChanged.connect(
            lambda _index: self._add_parameter(feature, setting_picker.currentData())
        )
        card_layout.addWidget(setting_picker)
        return card

    def _change_feature_type(
        self,
        feature: dict,
        picker: QComboBox,
        selector_row: QWidget,
        selector_edit: QLineEdit,
        index: int,
    ) -> None:
        selector = picker.itemData(index)
        if selector == "__custom__":
            feature["label"] = "Something else..."
            feature["custom"] = True
            feature["selector"] = ""
            selector_edit.clear()
            selector_row.setVisible(True)
        else:
            feature["label"] = picker.itemText(index)
            feature["custom"] = False
            feature["selector"] = selector
            selector_row.setVisible(False)
        self._write_feature(feature)

    def _set_custom_selector(self, feature: dict, selector: str) -> None:
        feature["selector"] = selector
        self._write_feature(feature)

    def _remove_feature(self, feature: dict) -> None:
        self.features.remove(feature)
        self._remove_feature_source(feature["id"])
        self._render_features()

    def _add_parameter(self, feature: dict, property_name: str) -> None:
        if not property_name:
            return
        if any(item["name"] == property_name for item in feature["parameters"]):
            return
        feature["parameters"].append(
            {"name": property_name, "value": DEFAULT_VALUES[property_name]}
        )
        self._write_feature(feature)
        self._render_features()

    def _parameter_row(self, feature: dict, parameter: dict) -> QWidget:
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(4, 0, 0, 0)
        property_name = parameter["name"]
        label = PROPERTY_LABELS.get(property_name, property_name)
        name_label = QLabel(label)
        name_label.setObjectName("themePropertyName")
        row_layout.addWidget(name_label)

        if property_name in COLOR_PROPERTIES:
            value_label = QLabel(parameter["value"])
            color_button = QPushButton("Choose")
            color_button.setObjectName("themeColorButton")
            color_button.setToolTip(f"Choose {label.lower()}")
            self._set_color_swatch(color_button, parameter["value"])
            color_button.clicked.connect(
                lambda: self._choose_color(feature, parameter, color_button, value_label)
            )
            row_layout.addWidget(color_button)
            row_layout.addWidget(value_label)
        elif property_name == "font-family":
            font_picker = QFontComboBox()
            font_picker.setCurrentFont(QFont(parameter["value"]))
            font_picker.currentFontChanged.connect(
                lambda font: self._set_parameter_value(feature, parameter, font.family())
            )
            row_layout.addWidget(font_picker, 1)
        elif property_name == "font-size" or property_name in NUMERIC_PROPERTIES:
            number, unit = self._parse_number(parameter["value"])
            number_picker = QSpinBox()
            number_picker.setRange(-1000 if property_name == "margin" else 0, 1000)
            number_picker.setValue(number)
            unit_picker = QComboBox()
            unit_picker.addItems(("pt", "px") if property_name == "font-size" else ("px", "%"))
            unit_index = unit_picker.findText(unit)
            if unit_index >= 0:
                unit_picker.setCurrentIndex(unit_index)

            def update_number(*_args) -> None:
                self._set_parameter_value(
                    feature,
                    parameter,
                    f"{number_picker.value()}{unit_picker.currentText()}",
                )

            number_picker.valueChanged.connect(update_number)
            unit_picker.currentTextChanged.connect(update_number)
            row_layout.addWidget(number_picker)
            row_layout.addWidget(unit_picker)
        elif property_name == "font-weight":
            value_picker = QComboBox()
            for text, value in (
                ("Normal", "normal"),
                ("Medium", "medium"),
                ("Semibold", "600"),
                ("Bold", "bold"),
            ):
                value_picker.addItem(text, value)
            self._select_combo_data(value_picker, parameter["value"])
            value_picker.currentIndexChanged.connect(
                lambda _index: self._set_parameter_value(
                    feature, parameter, value_picker.currentData()
                )
            )
            row_layout.addWidget(value_picker, 1)
        elif property_name == "text-align":
            value_picker = QComboBox()
            for text, value in (
                ("Left", "left"),
                ("Center", "center"),
                ("Right", "right"),
                ("Justify", "justify"),
            ):
                value_picker.addItem(text, value)
            self._select_combo_data(value_picker, parameter["value"])
            value_picker.currentIndexChanged.connect(
                lambda _index: self._set_parameter_value(
                    feature, parameter, value_picker.currentData()
                )
            )
            row_layout.addWidget(value_picker, 1)
        elif property_name == "border-style":
            value_picker = QComboBox()
            value_picker.addItems(("none", "solid", "dotted", "dashed", "double"))
            value_picker.setCurrentText(parameter["value"])
            value_picker.currentTextChanged.connect(
                lambda value: self._set_parameter_value(feature, parameter, value)
            )
            row_layout.addWidget(value_picker, 1)
        elif property_name == "border":
            value_picker = QComboBox()
            for text, value in (
                ("No border", "none"),
                ("Subtle border", "1px solid #c9c1b0"),
                ("Accent border", "1px solid #a6813e"),
                ("Strong border", "2px solid #496452"),
            ):
                value_picker.addItem(text, value)
            self._select_combo_data(value_picker, parameter["value"])
            value_picker.currentIndexChanged.connect(
                lambda _index: self._set_parameter_value(
                    feature, parameter, value_picker.currentData()
                )
            )
            row_layout.addWidget(value_picker, 1)
        else:
            value_edit = QLineEdit(parameter["value"])
            value_edit.textChanged.connect(
                lambda value: self._set_parameter_value(feature, parameter, value)
            )
            row_layout.addWidget(value_edit, 1)

        remove_button = QPushButton("Remove")
        remove_button.clicked.connect(
            lambda: self._remove_parameter(feature, parameter)
        )
        row_layout.addWidget(remove_button)
        return row

    @staticmethod
    def _select_combo_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value)
        if index < 0:
            combo.addItem(value, value)
            index = combo.count() - 1
        combo.setCurrentIndex(index)

    @staticmethod
    def _parse_number(value: str) -> tuple[int, str]:
        match = re.fullmatch(r"\s*(-?\d+)\s*([a-z%]*)\s*", value)
        if not match:
            return 10, "px"
        return int(match.group(1)), match.group(2) or "px"

    @staticmethod
    def _set_color_swatch(button: QPushButton, value: str) -> None:
        color = QColor(value)
        if not color.isValid():
            color = QColor("#ffffff")
        swatch = QPixmap(16, 16)
        swatch.fill(color)
        button.setIcon(QIcon(swatch))

    def _choose_color(
        self, feature: dict, parameter: dict, button: QPushButton, label: QLabel
    ) -> None:
        color = QColorDialog.getColor(QColor(parameter["value"]), self, "Choose color")
        if color.isValid():
            value = color.name()
            parameter["value"] = value
            label.setText(value)
            self._set_color_swatch(button, value)
            self._write_feature(feature)

    def _set_parameter_value(
        self, feature: dict, parameter: dict, value: str
    ) -> None:
        parameter["value"] = str(value)
        self._write_feature(feature)

    def _remove_parameter(self, feature: dict, parameter: dict) -> None:
        feature["parameters"].remove(parameter)
        self._write_feature(feature)
        self._render_features()

    def _write_feature(self, feature: dict) -> None:
        feature_id = feature["id"]
        marker = rf"/\* {FEATURE_MARKER} START {re.escape(feature_id)} \*/.*?/\* {FEATURE_MARKER} END {re.escape(feature_id)} \*/"
        properties = "\n".join(
            f"    {parameter['name']}: {parameter['value']};"
            for parameter in feature["parameters"]
        )
        selector = feature["selector"].strip()
        rule = f"\n{selector} {{\n{properties}\n}}" if selector else ""
        block = (
            f"/* {FEATURE_MARKER} START {feature_id} */{rule}\n"
            f"/* {FEATURE_MARKER} END {feature_id} */"
        )
        stylesheet, count = re.subn(
            marker,
            lambda _match: block,
            self.stylesheet,
            count=1,
            flags=re.DOTALL,
        )
        if not count:
            stylesheet = f"{self.stylesheet.rstrip()}\n\n{block}\n"
        self._set_source_from_feature(stylesheet)

    def _remove_feature_source(self, feature_id: str) -> None:
        marker = rf"/\* {FEATURE_MARKER} START {re.escape(feature_id)} \*/.*?/\* {FEATURE_MARKER} END {re.escape(feature_id)} \*/"
        stylesheet = re.sub(marker, "", self.stylesheet, count=1, flags=re.DOTALL)
        self._set_source_from_feature(stylesheet)

    def _set_source_from_feature(self, stylesheet: str) -> None:
        blocker = QSignalBlocker(self.raw_editor)
        self.raw_editor.setPlainText(stylesheet)
        del blocker
        self.stylesheetChanged.emit(self.stylesheet)

    def _remove_feature(self, feature: dict) -> None:
        self.features.remove(feature)
        self._remove_feature_source(feature["id"])
        self._render_features()

    def reset_stylesheet(self, stylesheet: str) -> None:
        self.features.clear()
        self.set_stylesheet(stylesheet)

    def _emit_stylesheet_changed(self, *_args) -> None:
        self.stylesheetChanged.emit(self.stylesheet)