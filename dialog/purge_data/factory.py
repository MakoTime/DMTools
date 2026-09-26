from .model import PurgeDataModel
from .view import PurgeDataView


def create_purge_data_dialog(parent=None):
    return PurgeDataView(PurgeDataModel(), parent=parent)