from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel

from dialog.rule_detail.factory import create_rule_detail_dialog


def test_rule_detail_text_is_selectable():
    QApplication.instance() or QApplication([])
    dialog = create_rule_detail_dialog(
        "simple_melee",
        "weapons-groups",
        ("weapon_category",),
        related_entities=(
            ("Club", "dmtools://rule/weapons-types/club"),
        ),
    )

    labels = dialog.findChildren(QLabel)
    description = next(label for label in labels if label.text().startswith("Simple melee"))
    related = next(label for label in labels if "Club" in label.text())
    selectable = (
        Qt.TextInteractionFlag.TextSelectableByMouse
        | Qt.TextInteractionFlag.TextSelectableByKeyboard
    )

    assert description.textInteractionFlags() & selectable == selectable
    assert related.textInteractionFlags() & selectable == selectable
    dialog.close()