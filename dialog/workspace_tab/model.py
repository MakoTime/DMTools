from dataclasses import dataclass


@dataclass
class WorkspaceTabModel:
    title: str
    can_restore: bool = False
    is_attached: bool = False

    def attach(self):
        if self.is_attached:
            raise RuntimeError("Workspace tab is already attached")
        self.is_attached = True

    def detach(self):
        self.is_attached = False

    def set_title(self, title):
        self.title = title