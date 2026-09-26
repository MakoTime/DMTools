from types import SimpleNamespace

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from dialog.manual_references.model import ManualReferencesModel
from dialog.manual_references.view import ManualReferencesView


class FakeStore:
    def __init__(self, rows):
        self.rows = tuple(rows)

    def all_records(self):
        return self.rows


class FakeController:
    def __init__(self, stores):
        self.stores = stores
        self.project = SimpleNamespace(
            blocks=SimpleNamespace(contains=lambda uid: uid in {
                f"dmtools-{namespace}-entity-database"
                for namespace in stores
            })
        )
        self.resolved = []

    def entity_database_store(self, namespace):
        return self.stores[namespace]

    def resolve_unresolved_reference(self, entity_type, display_fallback, target_uid):
        self.resolved.append((entity_type, display_fallback, target_uid))
        return ("source-uid",)


def row(uid, name, entity_type, namespace, metadata=None):
    return SimpleNamespace(
        uid=uid,
        name=name,
        entity_type=entity_type,
        source_namespace=namespace,
        source_metadata=metadata or {},
    )


def test_manual_references_lists_resolved_and_unresolved_across_namespaces():
    fireball = row("spell-fireball", "Fireball", "spell", "compendium")
    wand = row(
        "item-wand",
        "Wand",
        "item",
        "homebrew",
        {
            "entity_references": [{
                "path": "magic_item.spells[0]",
                "entity_type": "spell",
                "display_fallback": "Fireball",
                "target_uid": fireball.uid,
                "source_namespace": "compendium",
            }],
            "manual_entity_references": [{
                "path": "description",
                "entity_type": "spell",
                "display_fallback": "Fireball",
                "target_uid": fireball.uid,
                "source_namespace": "compendium",
            }],
            "reference_diagnostics": [{
                "path": "description",
                "entity_type": "spell",
                "display_fallback": "Missing Spell",
                "status": "missing",
            }],
        },
    )
    controller = FakeController({
        "compendium": FakeStore([fireball]),
        "homebrew": FakeStore([wand]),
    })

    model = ManualReferencesModel(controller)

    assert len(model.filtered_references("all")) == 3
    assert len(model.filtered_references("resolved")) == 2
    assert len(model.filtered_references("manual")) == 1
    unresolved = model.filtered_references("unresolved")[0]
    model.selected_reference = unresolved
    assert all(
        candidate.entity_type == "spell"
        for candidate in model.filtered_candidates(
            entity_type=unresolved.reference_type
        )
    )
    model.resolve(fireball.uid)
    assert controller.resolved == [("spell", "Missing Spell", fireball.uid)]


def test_manual_references_opens_selected_source_entity():
    QApplication.instance() or QApplication([])
    source = row("item-source", "Source Item", "item", "homebrew")
    target = row("spell-target", "Target Spell", "spell", "compendium")
    source.source_metadata = {
        "manual_entity_references": [{
            "path": "description",
            "entity_type": "spell",
            "display_fallback": "Target Spell",
            "target_uid": target.uid,
            "source_namespace": "compendium",
        }],
        "reference_diagnostics": [{
            "path": "higher_level",
            "entity_type": "spell",
            "display_fallback": "Missing Spell",
            "status": "missing",
        }],
    }
    controller = FakeController({
        "compendium": FakeStore([target]),
        "homebrew": FakeStore([source]),
    })
    controller.resolve_entity = lambda uid: {
        source.uid: source,
        target.uid: target,
    }[uid]
    opened = []
    view = ManualReferencesView(
        ManualReferencesModel(controller),
        on_open_entity=opened.append,
    )

    assert view.isModal() is False
    assert view.status_combo.currentData() == "unresolved"
    assert view.reference_list.selectionMode().name == "SingleSelection"
    assert not view.reference_list.item(0).flags() & Qt.ItemFlag.ItemIsUserCheckable
    assert view.candidate_list.selectionMode().name == "MultiSelection"
    assert view.candidate_type_combo.currentData() == "spell"
    view.candidate_type_combo.setCurrentIndex(0)
    assert view.candidate_type_combo.currentData() is None
    view.status_combo.setCurrentIndex(3)
    assert view.candidate_list.item(0).flags() & Qt.ItemFlag.ItemIsUserCheckable
    assert view.target_label.text() == ""
    assert view.open_match_button.isEnabled() is False
    view._open_source_entity()

    assert opened == [source]
    view.status_combo.setCurrentIndex(2)
    assert view.open_match_button.isEnabled() is True
    view._open_match_entity()
    assert opened == [source, target]
    view.close()


def test_manual_references_opens_selected_unresolved_candidate():
    QApplication.instance() or QApplication([])
    source = row(
        "monster-source",
        "Flamewrath",
        "monster",
        "compendium",
        {
            "reference_diagnostics": [{
                "path": "spells[0]",
                "entity_type": "spell",
                "display_fallback": "Fire Shield (See Wreathed in Flame)",
                "status": "missing",
            }],
        },
    )
    target = row("spell-target", "Fire Shield", "spell", "compendium")
    controller = FakeController({
        "compendium": FakeStore([source, target]),
        "homebrew": FakeStore([]),
    })
    controller.resolve_entity = lambda uid: {
        source.uid: source,
        target.uid: target,
    }[uid]
    opened = []
    view = ManualReferencesView(
        ManualReferencesModel(controller),
        on_open_entity=opened.append,
    )

    view.status_combo.setCurrentIndex(3)
    candidate = view.candidate_list.item(0)
    candidate.setCheckState(Qt.CheckState.Checked)

    assert view.open_match_button.isEnabled() is True
    view._open_match_entity()
    assert opened == [target]
    view.close()
