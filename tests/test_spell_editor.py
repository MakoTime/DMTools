import pytest
from PySide6.QtCore import QEvent, QObject
from PySide6.QtWidgets import QApplication, QWidget

from application.imports.registry import ENTITY_REGISTRY
from application.homebrew import HomebrewDraft
from dialog.homebrew.spell_editor.dialogs import EffectDialog, EffectsDialog, GrantDialog
from dialog.homebrew.spell_editor.model import SpellPropertyEditorModel
from dialog.homebrew.spell_editor.view import CheckableComboBox, SpellPropertyEditorView


def qt_app():
    return QApplication.instance() or QApplication([])


def _visible(widget):
    return not widget.isHidden()


def test_checkable_combo_shows_selected_values():
    qt_app()
    combo = CheckableComboBox(("verbal", "somatic", "material"), ("verbal",))

    assert combo.values() == ["verbal"]
    assert combo.lineEdit().text() == "verbal"

    combo.model().item(2).setCheckState(2)
    assert combo.values() == ["verbal", "material"]
    assert combo.lineEdit().text() == "verbal, material"


def test_grant_fields_follow_selected_grant_type():
    qt_app()
    dialog = GrantDialog({"type": "resistance"})
    dialog.show()

    assert _visible(dialog._fields["damage_type"][0])
    assert not _visible(dialog._fields["sense"][0])
    assert not _visible(dialog._fields["movement_type"][0])

    dialog.type.setCurrentText("sense")
    assert not _visible(dialog._fields["damage_type"][0])
    assert _visible(dialog._fields["sense"][0])
    assert _visible(dialog._fields["distance"][0])

    dialog.type.setCurrentText("movement")
    assert _visible(dialog._fields["movement_type"][0])
    assert _visible(dialog._fields["distance"][0])
    dialog.close()


def test_effect_fields_follow_selected_effect_type():
    qt_app()
    dialog = EffectDialog({"description": "Burning"})
    dialog.show()

    dialog.type.setCurrentText("damage")
    assert _visible(dialog._fields["damage_type"][0])
    assert _visible(dialog._fields["roll_dice"][0])
    assert _visible(dialog._fields["roll_count"][0])
    assert not _visible(dialog._fields["description"][0])

    dialog.type.setCurrentText("condition")
    assert _visible(dialog._fields["condition"][0])
    assert not _visible(dialog._fields["damage_type"][0])
    dialog.close()


@pytest.mark.parametrize("value", [
    None,
    {"description": "Burning"},
    {"damage": {"type": "fire", "roll": {"count": 1, "dice": 6}}},
    {"attack_hit": {"type": "melee_spell"}},
    {"grants": []},
])
def test_effect_constructor_does_not_show_windows(value):
    app = qt_app()
    shown_windows = []

    class ShowProbe(QObject):
        def eventFilter(self, watched, event):
            if (
                event.type() == QEvent.Type.Show
                and isinstance(watched, QWidget)
                and watched.isWindow()
            ):
                shown_windows.append(type(watched).__name__)
            return False

    probe = ShowProbe()
    app.installEventFilter(probe)
    try:
        dialog = EffectDialog(value)
        try:
            assert shown_windows == []
            assert not dialog.isVisible()
            if value and "damage" in value:
                assert _visible(dialog.roll_dice)
                assert _visible(dialog.roll_count)
                assert not _visible(dialog.roll_modifier)
        finally:
            dialog.close()
    finally:
        app.removeEventFilter(probe)


def test_target_range_rows_follow_targeting_selection():
    qt_app()
    payload = HomebrewDraft.blank("spell").payload
    view = SpellPropertyEditorView(SpellPropertyEditorModel.from_payload(payload))
    view.show()

    view.targeting_combo.setCurrentText("self")
    assert not _visible(view.target_range_amount_label)
    assert not _visible(view.target_range_amount)
    assert not _visible(view.target_range_unit_label)
    assert not _visible(view.target_range_unit)

    view.targeting_combo.setCurrentText("range")
    assert _visible(view.target_range_amount_label)
    assert _visible(view.target_range_amount)
    assert _visible(view.target_range_unit_label)
    assert _visible(view.target_range_unit)
    view.close()


def test_effects_dialog_uses_recursive_tree():
    qt_app()
    dialog = EffectsDialog([], parent=None)
    assert [dialog.tree.headerItem().text(index) for index in range(2)] == [
        "Effect",
        "Summary",
    ]
    dialog.close()


def test_effects_tree_contains_recursive_attack_effects():
    qt_app()
    dialog = EffectsDialog(
        [
            {
                "attack_hit": {
                    "type": "melee_spell",
                    "effects": [{"condition": "stunned"}],
                }
            }
        ]
    )

    assert dialog.tree.topLevelItemCount() == 1
    root = dialog.tree.topLevelItem(0)
    assert root.childCount() == 1
    assert root.child(0).text(0) == "condition"
    dialog.close()


def test_nested_dialogs_use_ok_not_apply():
    qt_app()
    dialog = EffectsDialog([])
    buttons = dialog.buttons.buttons()
    assert {button.text() for button in buttons} == {"OK", "Cancel"}
    dialog.close()


def test_damage_effect_constructor_produces_schema_valid_spell_payload():
    qt_app()
    dialog = EffectDialog()
    dialog.show()
    dialog.type.setCurrentText("damage")
    dialog.damage_type.setCurrentText("fire")
    dialog.roll_mode.setCurrentText("dice")
    dialog.roll_dice.setCurrentText("6")
    dialog.roll_count.setValue(1)
    dialog.apply_values()

    payload = {
        "name": "Test Spell",
        "description": "A test spell.",
        "level": 1,
        "casting_time": {"unit": "action"},
        "components": ["verbal"],
        "duration": {"duration": "instantaneous"},
        "effects": [dialog.value],
    }
    ENTITY_REGISTRY["spell"].validate_payload(payload)
    dialog.close()
