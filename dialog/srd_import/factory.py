from .model import SRDImportModel
from .view import SRDImportView


def create_srd_import_dialog(client, parent=None):
    collections = client.collections()
    model = SRDImportModel(
        collections=collections,
        query_options={name: client.query_options(name) for name in collections},
        collection=collections[0] if collections else "",
    )
    return SRDImportView(model, parent=parent)
