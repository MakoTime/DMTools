import pytest
from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import (
    QApplication,
    QDialogButtonBox,
    QPushButton,
    QTextEdit,
    QWidget,
)

from application.imports.registry import ENTITY_REGISTRY
from application.homebrew import HomebrewDraft
from dialog.homebrew.spell_editor.dialogs import EffectDialog, EffectsDialog, GrantDialog
from dialog.homebrew.spell_editor.model import SpellPropertyEditorModel
from dialog.homebrew.spell_editor.view import CheckableComboBox, SpellPropertyEditorView


def qt_app():
    return QApplication.instance() or QApplication([])


def _visible(widget):
    return not widget.isHidden()


def _process_events():
    QApplication.processEvents()


def _dialog(title, exclude=()):
    _process_events()
    return next(
        widget for widget in QApplication.topLevelWidgets()
        if (
            widget.windowTitle() == title
            and widget.isVisible()
            and widget not in exclude
        )
    )


def _click_button(widget, text):
    button = next(
        button for button in widget.findChildren(QPushButton)
        if button.text() == text
    )
    button.click()
    _process_events()


def _choose_combo(combo, text):
    combo.showPopup()
    _process_events()
    index = combo.findText(text)
    assert index >= 0
    item_rect = combo.view().visualRect(combo.model().index(index, 0))
    QTest.mouseClick(
        combo.view().viewport(),
        Qt.MouseButton.LeftButton,
        pos=item_rect.center(),
    )
    _process_events()


def _set_spinbox(spinbox, value):
    spinbox.setFocus()
    spinbox.selectAll()
    QTest.keyClicks(spinbox, str(value))
    QTest.keyClick(spinbox, Qt.Key.Key_Enter)
    _process_events()


def _set_line_edit(widget, value):
    widget.setFocus()
    widget.selectAll()
    lines = value.split("\n") if isinstance(widget, QTextEdit) else [value]
    for index, line in enumerate(lines):
        QTest.keyClicks(widget, line)
        if index < len(lines) - 1:
            QTest.keyClick(widget, Qt.Key.Key_Return)
    _process_events()


def test_checkable_combo_shows_selected_values():
    qt_app()
    combo = CheckableComboBox(("verbal", "somatic", "material"), ("verbal",))

    assert combo.values() == ["verbal"]
    assert combo.lineEdit().text() == "verbal"

    combo.model().item(2).setCheckState(Qt.CheckState.Checked)
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


@pytest.mark.parametrize(
    ("effect_type", "visible_fields", "visible_controls"),
    [
        ("damage", {"damage_type", "roll_mode", "roll_dice", "roll_count", "damage_modifier", "damage_ability"}, set()),
        ("healing", {"roll_mode", "roll_dice", "roll_count"}, set()),
        ("ability_score", {"ability"}, set()),
        ("attack_hit", {"attack_type", "attack_bonus"}, {"attack_hit_effects_button"}),
        ("attack_save", {"ability"}, {"attack_save_success_button", "attack_save_failure_button"}),
        ("condition", {"condition"}, set()),
        ("grants", set(), {"grants_button"}),
        ("description", {"description"}, set()),
    ],
)
def test_effect_type_shows_only_relevant_fields(effect_type, visible_fields, visible_controls):
    qt_app()
    dialog = EffectDialog()
    dialog.show()
    dialog.type.setCurrentText(effect_type)

    for name, (_label, widget) in dialog._fields.items():
        assert _visible(widget) is (name in visible_fields), name
        assert _visible(_label) is (name in visible_fields), name
    for name in (
        "attack_hit_effects_button",
        "attack_save_success_button",
        "attack_save_failure_button",
        "grants_button",
    ):
        assert _visible(getattr(dialog, name)) is (name in visible_controls), name
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


def test_effect_editor_preserves_schema_supported_roll_and_attack_fields():
    qt_app()
    damage = EffectDialog({
        "damage": {
            "type": "fire",
            "roll": {"ability": "intelligence"},
            "modifier": 2,
            "ability": "charisma",
        }
    })
    damage.apply_values()
    attack = EffectDialog({
        "attack_hit": {"type": "melee_spell", "bonus": 3},
    })
    attack.apply_values()
    saving_throw = EffectDialog({
        "attack_save": {"ability": "wisdom", "dc": 15},
    })
    saving_throw.apply_values()

    assert damage.value["damage"] == {
        "type": "fire",
        "roll": {"ability": "intelligence"},
        "modifier": 2,
        "ability": "charisma",
    }
    assert attack.value["attack_hit"]["bonus"] == 3
    assert saving_throw.value["attack_save"]["dc"] == 15
    damage.close()
    attack.close()
    saving_throw.close()


def test_blank_spell_editor_produces_schema_valid_payload():
    qt_app()
    payload = HomebrewDraft.blank("spell").payload
    view = SpellPropertyEditorView(SpellPropertyEditorModel.from_payload(payload))

    view.update_model()

    ENTITY_REGISTRY["spell"].validate_payload(view.model.payload)
    assert view.model.payload["components"] == ["verbal"]
    assert "school" not in view.model.payload
    assert "classes" not in view.model.payload
    assert "tags" not in view.model.payload
    view.close()


def test_target_editor_preserves_schema_supported_target_fields():
    qt_app()
    payload = HomebrewDraft.blank("spell").payload
    payload["target"] = {
        "targeting": "self",
        "type": "creatures",
        "count": {"maximum": 2},
        "zone": {"type": "sphere", "size": 20},
    }
    view = SpellPropertyEditorView(SpellPropertyEditorModel.from_payload(payload))

    view.update_model()

    assert view.model.payload["target"]["type"] == "creatures"
    assert view.model.payload["target"]["count"] == {"maximum": 2}
    assert view.model.payload["target"]["zone"] == {"type": "sphere", "size": 20}
    view.close()


def test_dialogs_create_ice_knife_payload():
    qt_app()
    description = (
        "You create a shard of ice and fling it at one creature within range. "
        "Make a ranged spell attack against the target. On a hit, the target "
        "takes 1d10 piercing damage. Hit or miss, the shard then explodes. "
        "The target and each creature within 5 feet of it must succeed on a "
        "Dexterity saving throw or take 2d6 cold damage.\n\n"
        "At Higher Levels: When you cast this spell using a spell slot of 2nd "
        "level or higher, the cold damage increases by 1d6 for each slot level "
        "above 1st.\n\n"
        "Elemental Evil Player's Companion, p. 19\n\n"
        "Princes of the Apocalypse, p. 237"
    )
    payload = HomebrewDraft.blank("spell").payload
    view = SpellPropertyEditorView(SpellPropertyEditorModel.from_payload(payload))

    _set_line_edit(view.name_edit, "Ice Knife")
    _set_line_edit(view.description_edit, description)
    _set_spinbox(view.level_spin, 1)
    _choose_combo(view.school_combo, "conjuration")
    _set_spinbox(view.casting_amount, 1)
    _choose_combo(view.casting_unit, "action")
    _choose_combo(view.targeting_combo, "range")
    _set_spinbox(view.target_range_amount, 60)
    _set_line_edit(view.target_range_unit, "feet")
    _choose_combo(view.duration_unit, "instantaneous")
    for name in ("verbal", "somatic", "material"):
        _choose_combo(view.components_combo, name)
    for name in ("druid", "sorcerer", "wizard"):
        _choose_combo(view.classes_combo, name)
    _set_line_edit(view.material_description, "a drop of water or a piece of ice")

    view.effects_button.click()
    effects = _dialog("Spell Effects")
    _click_button(effects, "Add Effect")
    save = effects.effect_editor
    _choose_combo(save.type, "attack_save")
    _set_line_edit(save.ability.lineEdit(), "dexterity")
    effects.save_effect.click()
    _process_events()
    effects.tree.setCurrentItem(effects.tree.topLevelItem(0))
    _choose_combo(effects.child_collection, "Save failure")

    def add_damage(damage_type, dice, count):
        _choose_combo(effects.child_collection, "Save failure")
        effects.add_child.click()
        damage = effects.effect_editor
        _choose_combo(damage.type, "damage")
        _choose_combo(damage.damage_type, damage_type)
        _set_line_edit(damage.roll_dice.lineEdit(), str(dice))
        _set_spinbox(damage.roll_count, count)
        effects.save_effect.click()
        _process_events()

    add_damage("piercing", 10, 1)
    add_damage("cold", 6, 2)
    effects.buttons.button(QDialogButtonBox.StandardButton.Ok).click()
    _process_events()
    view.update_model()

    assert view.model.payload == {
        "casting_time": {"amount": 1, "unit": "action"},
        "classes": ["druid", "sorcerer", "wizard"],
        "components": ["somatic", "material"],
        "concentration": False,
        "description": description,
        "duration": {"duration": "instantaneous"},
        "effects": [{
            "attack_save": {
                "ability": "dexterity",
                "failure": [
                    {"damage": {"modifier": 0, "roll": {"count": 1, "dice": 10}, "type": "piercing"}},
                    {"damage": {"modifier": 0, "roll": {"count": 2, "dice": 6}, "type": "cold"}},
                ],
            }
        }],
        "level": 1,
        "material": {"consumed": False, "description": "a drop of water or a piece of ice"},
        "name": "Ice Knife",
        "ritual": False,
        "school": "conjuration",
        "target": {"range": {"amount": 60, "unit": "feet"}, "targeting": "range"},
    }
    ENTITY_REGISTRY["spell"].validate_payload(view.model.payload)
    view.close()
