from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from dialog.manual_references import create_manual_references_dialog
from dialog.purge_data.factory import create_purge_data_dialog


def setup_menu(
	main_window,
	import_controller=None,
	project_controller=None,
	*,
	on_open_entity=None,
):
	"""Populate the menus created by the main window UI."""
	file_menu = main_window.menuFile
	edit_menu = main_window.menuEdit
	data_menu = main_window.menuBar().addMenu("Data")
	display_space = getattr(main_window, "display_space_controller", None)

	open_action = QAction("Open Project", main_window)
	save_action = QAction("Save", main_window)
	save_as_action = QAction("Save As...", main_window)
	exit_action = QAction("Exit", main_window)
	exit_action.triggered.connect(main_window.close)

	file_menu.addAction(open_action)
	file_menu.addAction(save_action)
	file_menu.addAction(save_as_action)
	import_menu = file_menu.addMenu("Import")
	import_xml_action = import_menu.addAction("Import from XML")
	import_json_action = import_menu.addAction("Import from JSON")
	srd_menu = import_menu.addMenu("Import from 5eSRD Online")
	srd_all_action = srd_menu.addAction("All")
	srd_custom_action = srd_menu.addAction("Custom...")
	srd_collection_actions = {}
	for collection in ("monsters", "spells", "classes", "races", "backgrounds", "feats", "equipment"):
		action = srd_menu.addAction(collection.title())
		srd_collection_actions[collection] = action
	if import_controller is None:
		import_xml_action.setEnabled(False)
		import_json_action.setEnabled(False)
		srd_all_action.setEnabled(False)
		srd_custom_action.setEnabled(False)
		for action in srd_collection_actions.values():
			action.setEnabled(False)
	else:
		import_xml_action.setEnabled(import_controller.can_import)
		import_json_action.setEnabled(import_controller.can_import)
		import_xml_action.triggered.connect(import_controller.import_xml)
		import_json_action.triggered.connect(import_controller.import_json)
		for action, method_name in (
			(srd_all_action, "import_srd_all"),
			(srd_custom_action, "import_srd_custom"),
		):
			method = getattr(import_controller, method_name, None)
			action.setEnabled(import_controller.can_import and callable(method))
			if callable(method):
				action.triggered.connect(method)
		for collection, action in srd_collection_actions.items():
			method = getattr(import_controller, "import_srd_collection", None)
			action.setEnabled(import_controller.can_import and callable(method))
			if callable(method):
				action.triggered.connect(
					lambda checked=False, collection=collection: method(collection)
				)
	file_menu.addSeparator()
	file_menu.addAction(exit_action)

	undo_action = edit_menu.addAction("Undo")
	redo_action = edit_menu.addAction("Redo")
	undo_action.setEnabled(False)
	redo_action.setEnabled(False)
	normalize_references_action = data_menu.addAction("Normalise References")
	normalize_references_action.setEnabled(project_controller is not None)
	if project_controller is not None:
		normalize_references_action.triggered.connect(
			lambda: project_controller.normalize_entity_references(parent=main_window)
		)
	manual_references_action = data_menu.addAction("Manual References")
	manual_references_action.setEnabled(project_controller is not None)
	if project_controller is not None:
		def open_manual_references():
			dialog = getattr(main_window, "manual_references_dialog", None)
			if dialog is None:
				dialog = create_manual_references_dialog(
					project_controller,
					on_open_entity=on_open_entity,
					parent=main_window,
				)
				main_window.manual_references_dialog = dialog
			dialog.show()
			dialog.raise_()
			dialog.activateWindow()

		manual_references_action.triggered.connect(open_manual_references)
	purge_menu = data_menu.addMenu("Purge Data")
	purge_compendium_action = purge_menu.addAction("Compendium")
	purge_homebrew_action = purge_menu.addAction("Homebrew")
	purge_custom_action = purge_menu.addAction("Custom...")
	if project_controller is None:
		for action in (purge_compendium_action, purge_homebrew_action, purge_custom_action):
			action.setEnabled(False)
	else:
		def purge_namespace(namespace):
			label = namespace.title()
			answer = QMessageBox.question(
				main_window,
				"Purge Entity Data",
				f"Permanently delete all {label} entity data?",
				QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
				QMessageBox.StandardButton.No,
			)
			if answer == QMessageBox.StandardButton.Yes:
				project_controller.purge_entity_data(namespace)

		purge_compendium_action.triggered.connect(
			lambda: purge_namespace("compendium")
		)
		purge_homebrew_action.triggered.connect(
			lambda: purge_namespace("homebrew")
		)
		def purge_custom():
			dialog = create_purge_data_dialog(main_window)
			if dialog.exec():
				project_controller.purge_entity_data(
					dialog.model.namespace, dialog.model.entity_types
				)
		purge_custom_action.triggered.connect(purge_custom)
	window_menu = main_window.menuBar().addMenu("Window")
	display_menu = window_menu.addMenu("Display Space")
	minimize_all_action = display_menu.addAction("Minimise all")
	rearrange_grid_action = display_menu.addAction("Rearrange grid")
	if display_space is None:
		minimize_all_action.setEnabled(False)
		rearrange_grid_action.setEnabled(False)
	else:
		minimize_all_action.triggered.connect(display_space.minimize_all)
		rearrange_grid_action.triggered.connect(display_space.rearrange_grid)

	main_window.open_action = open_action
	main_window.save_action = save_action
	main_window.save_as_action = save_as_action
	main_window.exit_action = exit_action
	main_window.import_xml_action = import_xml_action
	main_window.import_json_action = import_json_action
	main_window.srd_import_menu = srd_menu
	main_window.srd_import_all_action = srd_all_action
	main_window.srd_import_custom_action = srd_custom_action
	main_window.srd_import_collection_actions = srd_collection_actions
	main_window.undo_action = undo_action
	main_window.redo_action = redo_action
	main_window.data_menu = data_menu
	main_window.normalize_references_action = normalize_references_action
	main_window.manual_references_action = manual_references_action
	main_window.manual_references_dialog = None
	main_window.purge_data_menu = purge_menu
	main_window.purge_compendium_action = purge_compendium_action
	main_window.purge_homebrew_action = purge_homebrew_action
	main_window.purge_custom_action = purge_custom_action
	main_window.window_menu = window_menu
	main_window.display_space_menu = display_menu
	main_window.minimize_all_action = minimize_all_action
	main_window.rearrange_grid_action = rearrange_grid_action

	return {
		"open": open_action,
		"save": save_action,
		"save_as": save_as_action,
		"import_xml": import_xml_action,
		"import_json": import_json_action,
		"import_srd_all": srd_all_action,
		"import_srd_custom": srd_custom_action,
		"exit": exit_action,
		"undo": undo_action,
		"redo": redo_action,
		"normalize_references": normalize_references_action,
		"purge_compendium": purge_compendium_action,
		"purge_homebrew": purge_homebrew_action,
		"purge_custom": purge_custom_action,
		"minimize_all": minimize_all_action,
		"rearrange_grid": rearrange_grid_action,
	}
