from PySide6.QtWidgets import QToolButton


class SplitButton(QToolButton):
    """Button with a primary action and a dropdown menu."""

    def __init__(self, text="", menu=None, parent=None):
        super().__init__(parent)
        self.setText(text)
        self.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
        self.setMinimumHeight(self.fontMetrics().height() + 12)
        self.setMenu(menu)
