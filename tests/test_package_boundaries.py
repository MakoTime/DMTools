import importlib


def test_target_architecture_packages_are_importable_without_qt_side_effects():
    for package_name in ("core", "application", "views", "editors"):
        package = importlib.import_module(package_name)
        assert package.__package__ == package_name


def test_domain_core_does_not_import_presentation_packages():
    core = importlib.import_module("core")

    assert not hasattr(core, "PySide6")
    assert not hasattr(core, "PyVista")
