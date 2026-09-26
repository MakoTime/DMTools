import importlib

from projectfoundry import EditedObject

from objects.json_object import JSONDataObject
from objects.shopkeeper_object import ShopkeeperObject
from objects.table_object import TableDataObject


def test_durable_dmtools_wrappers_use_projectfoundry_edited_object_identity():
    wrappers = (
        JSONDataObject("JSON"),
        ShopkeeperObject("Shopkeeper"),
        TableDataObject("Table"),
    )

    assert all(isinstance(wrapper, EditedObject) for wrapper in wrappers)
    assert all(wrapper.guid for wrapper in wrappers)


def test_legacy_object_symbols_are_not_exported():
    module = importlib.import_module("objects")

    assert not hasattr(module, "ObjectBase")
    assert not hasattr(module, "ObjectData")
